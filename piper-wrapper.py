#!/usr/bin/env python3

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


HOST = "0.0.0.0"
PORT = 8082
PIPER_HOST = "127.0.0.1"
PIPER_PORT = 8083
PIPER_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "de_DE-thorsten-high.onnx")
API_KEY = os.environ.get("PIPER_ENV_KEY", "")
USE_GPU = os.environ.get("USE_GPU", "").lower() in ("1", "true", "yes", "on")

_piper_voices: dict[str, piper.voice.PiperVoice] = {}


def _discover_voices() -> dict[str, str]:
    mapping: dict[str, str] = {}
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    if not os.path.isdir(models_dir):
        return mapping
    for fname in os.listdir(models_dir):
        if fname.endswith(".onnx"):
            voice_name = fname.rsplit(".", 1)[0]  # strip extension
            mapping[voice_name] = os.path.join(models_dir, fname)
    return mapping


def _resolve_voice(voice_name: str) -> str | None:
    if voice_name == "default":
        return PIPER_MODEL
    mapping = _discover_voices()
    return mapping.get(voice_name)


def _get_voice(voice_name: str) -> piper.voice.PiperVoice:
    path = _resolve_voice(voice_name)
    if path is None:
        raise ValueError(f"Unbekannte Stimme: {voice_name}")
    if path not in _piper_voices:
        _piper_voices[path] = piper.voice.PiperVoice.load(path, use_cuda=USE_GPU)
    return _piper_voices[path]

_piper_ready = threading.Event()


def start_piper_http() -> None:
    _piper_voices.clear()
    _piper_voices[PIPER_MODEL] = piper.voice.PiperVoice.load(PIPER_MODEL, use_cuda=USE_GPU)
    print(f"Default voice loaded: {PIPER_MODEL} (GPU={'yes' if USE_GPU else 'no'})")

    voices = _discover_voices()
    print(f"Available voices: {', '.join(voices.keys())}")

    app = Flask(__name__)

    @app.route("/synthesize", methods=["POST"])
    def synthesize() -> tuple:
        body = request.get_data(as_text=True)
        try:
            data = json.loads(body)
            text = data.get("input", "")
            voice_name = data.get("voice", "default")
        except (json.JSONDecodeError, KeyError):
            return ("Invalid JSON", 400)

        if not text:
            return ("Missing 'input' field", 400)

        try:
            voice = _get_voice(voice_name)
        except ValueError as exc:
            return (str(exc), 400)


        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            voice.synthesize_wav(text, wav_file)

        wav_data = buf.getvalue()
        return (wav_data, 200, {"Content-Type": "audio/wav", "Content-Length": str(len(wav_data))})

    @app.route("/info", methods=["GET"])
    def info() -> tuple:
        return (json.dumps({"status": "ok"}), 200, {"Content-Type": "application/json"})

    _piper_ready.set()

    app.run(host=PIPER_HOST, port=PIPER_PORT, use_reloader=False, threaded=True)


bridge_app = Flask(__name__)


def _forward_synthesize(body: bytes) -> tuple:
    import urllib.request

    url = f"http://{PIPER_HOST}:{PIPER_PORT}/synthesize"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(url, data=body, timeout=30)
    wav_data = resp.read()
    return (wav_data, 200, {"Content-Type": "audio/wav", "Content-Length": str(len(wav_data))})


@bridge_app.route("/audio/speech", methods=["POST"])
def audio_speech() -> tuple:
    auth = request.headers.get("Authorization", "")
    if API_KEY and not auth.startswith("Bearer "):
        return ("unauthorized", 401, {"Content-Type": "text/plain"})
    if API_KEY and auth != f"Bearer {API_KEY}":
        return ("unauthorized", 401, {"Content-Type": "text/plain"})

    body = request.get_data()
    return _forward_synthesize(body)


def main() -> None:
    piper_thread = Thread(target=start_piper_http, daemon=True)
    piper_thread.start()


    if not _piper_ready.wait(timeout=10.0):
        print("ERROR: Piper did not become ready within timeout", file=sys.stderr)
        sys.exit(1)

    print(f"Piper ready on {PIPER_HOST}:{PIPER_PORT}")

    def handle_signal(signum, frame):
        print("\nShutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    bridge_app.run(host=HOST, port=PORT, use_reloader=False)


if __name__ == "__main__":
    main()