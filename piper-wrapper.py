#!/usr/bin/env python3
"""
Piper TTS Bridge für Open WebUI.

Mappt POST /audio/speech → /synthesize, startet Piper HTTP-Server
auf Port 8083 und bietet API-Key-Auth.
"""

import io
import json
import os
import signal
import sys
import threading
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from flask import Flask, request

import piper

# ─── Konfiguration ───────────────────────────────────────────────────────────

HOST = "0.0.0.0"
PORT = 8082
PIPER_HOST = "127.0.0.1"
PIPER_PORT = 8083
PIPER_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "de_DE-thorsten-high.onnx")
API_KEY = os.environ.get("PIPER_ENV_KEY", "")
USE_GPU = os.environ.get("USE_GPU", "").lower() in ("1", "true", "yes", "on")

# ─── Piper HTTP-Server (Flask) auf Port 8083 ─────────────────────────────────

_piper_voice: piper.voice.PiperVoice | None = None
_piper_ready = threading.Event()


def start_piper_http() -> None:
    """Startet einen Flask-Server auf Port 8083, der Piper-Synthese anbietet."""
    global _piper_voice

    # Voice laden
    _piper_voice = piper.voice.PiperVoice.load(PIPER_MODEL, use_cuda=USE_GPU)
    print(f"Voice loaded: {PIPER_MODEL} (GPU={'yes' if USE_GPU else 'no'})")

    app = Flask(__name__)

    @app.route("/synthesize", methods=["POST"])
    def synthesize() -> tuple:
        body = request.get_data(as_text=True)
        try:
            data = json.loads(body)
            text = data.get("input", "")
        except (json.JSONDecodeError, KeyError):
            return ("Invalid JSON", 400)

        if not text:
            return ("Missing 'input' field", 400)

        # Synthese
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            _piper_voice.synthesize_wav(text, wav_file)

        wav_data = buf.getvalue()
        return (wav_data, 200, {"Content-Type": "audio/wav", "Content-Length": str(len(wav_data))})

    @app.route("/info", methods=["GET"])
    def info() -> tuple:
        return (json.dumps({"status": "ok"}), 200, {"Content-Type": "application/json"})

    # Server ready signal
    _piper_ready.set()

    app.run(host=PIPER_HOST, port=PIPER_PORT, use_reloader=False, threaded=True)


# ─── Open WebUI Bridge-Flask-App auf Port 8082 ───────────────────────────────

bridge_app = Flask(__name__)


def _forward_synthesize(body: bytes) -> tuple:
    """Forward body to Piper HTTP-Server und gibt WAV zurück."""
    import urllib.request

    url = f"http://{PIPER_HOST}:{PIPER_PORT}/synthesize"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(url, data=body, timeout=30)
    wav_data = resp.read()
    return (wav_data, 200, {"Content-Type": "audio/wav", "Content-Length": str(len(wav_data))})


@bridge_app.route("/audio/speech", methods=["POST"])
def audio_speech() -> tuple:
    """Empfangt /audio/speech und leitet an Piper weiter."""
    # Auth-Check (Authorization: Bearer <key>)
    auth = request.headers.get("Authorization", "")
    if API_KEY and not auth.startswith("Bearer "):
        return ("unauthorized", 401, {"Content-Type": "text/plain"})
    if API_KEY and auth != f"Bearer {API_KEY}":
        return ("unauthorized", 401, {"Content-Type": "text/plain"})

    body = request.get_data()
    return _forward_synthesize(body)


# ─── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    # Piper HTTP-Server in separatem Thread starten
    piper_thread = Thread(target=start_piper_http, daemon=True)
    piper_thread.start()

    # Auf Piper-Ready warten
    if not _piper_ready.wait(timeout=10.0):
        print("ERROR: Piper did not become ready within timeout", file=sys.stderr)
        sys.exit(1)

    print(f"Piper ready on {PIPER_HOST}:{PIPER_PORT}")

    # Bridge-Server starten
    print(f"Bridge listening on http://{HOST}:{PORT}")

    # Graceful Shutdown via SIGINT / SIGTERM
    def handle_signal(signum, frame):
        print("\nShutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    bridge_app.run(host=HOST, port=PORT, use_reloader=False)


if __name__ == "__main__":
    main()