# CLAUDE.md

## Projekt

Piper TTS Bridge für Open WebUI — ein Flask-Wrapper, der Open WebUIs TTS-Endpunkt (`POST /audio/speech`) an einen lokalen Piper TTS-Server (Port 8083) weiterleitet.

## Architektur

```
piper-wrapper.py
├── start_piper_http()   → Piper HTTP-Server (Flask, Port 8083, /synthesize)
├── bridge_app           → Open WebUI Bridge (Flask, Port 8082, /audio/speech)
├── _forward_synthesize()→ Forward body an Piper HTTP, gibt WAV zurück
└── main()               → Thread startet Piper-Server, wartet auf ready, startet Bridge
```

- **Piper HTTP-Server** (Port 8083): Läuft im eigenen Thread, lädt Voice-Modell, antwortet auf `POST /synthesize` mit WAV.
- **Bridge-App** (Port 8082): Empfängt `/audio/speech`, prüft `X-API-Key`, forwarded Body an Piper.
- **Ready-Signal**: `_piper_ready` (`threading.Event`) statt Polling `/info`.
- **Shutdown**: `SIGINT`/`SIGTERM` → `sys.exit(0)`.

## Wichtige Konstanten

| Name | Wert | Bedeutung |
|------|------|-----------|
| `HOST` | `0.0.0.0` | Bridge-Listen-Adresse |
| `PORT` | `8082` | Bridge-Port |
| `PIPER_HOST` | `127.0.0.1` | Piper-Listen-Adresse |
| `PIPER_PORT` | `8083` | Piper-Port |
| `PIPER_MODEL` | `models/de_DE-thorsten-high.onnx` | Voice-Modell (109 MB) |
| `API_KEY` | `PIPER_ENV_KEY` (Env-Var) | Auth-Key |

## Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Starten
PIPER_ENV_KEY="mein_key" python piper-wrapper.py

# Test (OpenAI-Format: {"input": "..."})
curl -X POST -H "Content-Type: application/json" \
  -H "X-API-Key: mein_key" \
  -d '{"input": "Hallo Welt"}' \
  http://127.0.0.1:8082/audio/speech -o test.wav

# systemd-Service
sudo cp piper-wrapper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now piper-wrapper
```

## Open WebUI-Konfiguration

**Settings → Audio → Text-to-Speech:**

| Feld | Wert |
|------|------|
| Provider | `Custom` |
| URL | `http://localhost:8082/audio/speech` |
| API-Key | `mein_key` |
| Model | `de_DE-thorsten-high` |

## Hinweise

- `models/` ist von Git ausgeschlossen (.gitignore).
- `requests` wurde durch `flask` ersetzt (Body-Forward nutzt `urllib.request`).
- Der Bridge-Server erwartet OpenAI-kompatible Payloads: `{"input": "text"}`.
- Piper antwortet auf `/synthesize` mit `{"input": "text"}` (gleiches Format).
- `system.md` enthält Setup-Anleitung; `piper-wrapper.service` für systemd-Deployment.
- `piper-openwebui.iml` ist IntelliJ-IDEA-Projektdatei.