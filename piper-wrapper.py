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
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

import piper

# ─── Konfiguration ───────────────────────────────────────────────────────────

HOST = "0.0.0.0"
PORT = 8082
PIPER_HOST = "127.0.0.1"
PIPER_PORT = 8083
PIPER_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "de_DE-thorsten-high.onnx")
API_KEY = os.environ.get("PIPER_ENV_KEY", "")

# ─── Piper HTTP-Server (eigener kleiner Server auf Port 8083) ────────────────

_piper_voice: piper.voice.PiperVoice | None = None


def start_piper_http() -> None:
    """Startet einen HTTP-Server auf Port 8083, der Piper-Synthese anbietet."""
    global _piper_voice

    # Voice laden
    _piper_voice = piper.voice.PiperVoice.load(PIPER_MODEL)
    print(f"Voice loaded: {PIPER_MODEL}")

    class PiperHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != "/synthesize":
                self.send_error(404)
                return

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b""

            try:
                data = json.loads(body)
                input = data.get("input", "")
            except (json.JSONDecodeError, KeyError):
                self.send_error(400, "Invalid JSON")
                return

            if not input:
                self.send_error(400, "Missing 'input' field")
                return

            # Synthese
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                _piper_voice.synthesize_wav(input, wav_file)

            wav_data = buf.getvalue()

            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(wav_data)))
            self.end_headers()
            self.wfile.write(wav_data)

        def do_GET(self) -> None:
            if self.path == "/info":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            else:
                self.send_error(404)

        def log_message(self, fmt, *args):
            sys.stderr.write(f"[piper] {fmt % args}\n")

    server = HTTPServer((PIPER_HOST, PIPER_PORT), PiperHandler)
    server.serve_forever()


# ─── Open WebUI Bridge-Handler ──────────────────────────────────────────────

class BridgeHandler(BaseHTTPRequestHandler):
    """Empfangt /audio/speech und leitet an Piper weiter."""

    def do_POST(self) -> None:
        if self.path != "/audio/speech":
            self.send_error(404)
            return

        # Auth-Check
        if API_KEY and self.headers.get("X-API-Key") != API_KEY:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": "unauthorized"}')
            return

        # Body lesen und an Piper forwarden
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        try:
            import urllib.request

            url = f"http://{PIPER_HOST}:{PIPER_PORT}/synthesize"
            req = urllib.request.Request(url, data=body, method="POST")
            req.add_header("Content-Type", "application/json")
            resp = urllib.request.urlopen(url, data=body, timeout=30)
            wav_data = resp.read()

            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(wav_data)))
            self.end_headers()
            self.wfile.write(wav_data)
        except Exception as exc:
            self.send_error(502, f"Piper error: {exc}")

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[wrapper] {fmt % args}\n")


# ─── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    # Piper HTTP-Server in separatem Thread starten
    piper_thread = Thread(target=start_piper_http, daemon=True)
    piper_thread.start()

    # Auf Piper-Ready warten
    import time
    import urllib.request

    url = f"http://{PIPER_HOST}:{PIPER_PORT}/info"
    deadline = time.monotonic() + 10.0
    ready = False
    while time.monotonic() < deadline:
        try:
            resp = urllib.request.urlopen(url, timeout=2)
            if resp.status == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not ready:
        print("ERROR: Piper did not become ready within timeout", file=sys.stderr)
        sys.exit(1)

    print(f"Piper ready on {PIPER_HOST}:{PIPER_PORT}")

    # Bridge-Server starten
    server = HTTPServer((HOST, PORT), BridgeHandler)
    print(f"Bridge listening on http://{HOST}:{PORT}")

    # Graceful Shutdown
    def handle_signal(signum, frame):
        print("\nShutting down...")
        server.shutdown()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    server.serve_forever()


if __name__ == "__main__":
    main()
