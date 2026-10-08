# Piper TTS Bridge für Open WebUI

> ⚠️ **Hinweis:** Dieser Code wurde vollständig von einer KI generiert und nicht manuell geprüft.
> Nutze ihn auf eigene Gefahr und prüfe kritische Stellen (Auth, Network, TTS-Qualität) vor Produktiveinsatz.

Ein kleiner Flask-Wrapper, der Open WebUIs TTS-Endpunkt (`/audio/speech`) an einen lokalen Piper TTS-Server weiterleitet.

## Features

- **API-Endpunkt:** `POST /audio/speech` (Open WebUI Standard)
- **Piper HTTP-Server:** Läuft auf Port 8083, antwortet auf `/synthesize`
- **API-Key-Auth:** Über Umgebungsvariable `PIPER_ENV_KEY`
- **Graceful Shutdown:** Piper wird bei `Ctrl+C` sauber beendet

## Setup

```bash
# Virtual Environment
python -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt

# API-Key setzen
export PIPER_ENV_KEY="dein_geheimer_key"

# Wrapper starten
python piper-wrapper.py
```

## Open WebUI-Konfiguration

Unter **Settings → Audio → Text-to-Speech**:

| Feld | Wert |
|------|------|
| Provider | `Custom` |
| URL | `http://localhost:8082/audio/speech` |
| API-Key | `dein_geheimer_key` |
| Model | `de_DE-thorsten-high` |

## Port-Übersicht

| Dienst | Port |
|--------|------|
| Piper TTS HTTP | 8083 |
| Wrapper (Open WebUI Bridge) | 8082 |

## Test

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dein_geheimer_key" \
  -d '{"text": "Hallo Welt"}' \
  http://127.0.0.1:8082/audio/speech -o test.wav
```

## Struktur

```
piper-openwebui/
├── piper-wrapper.py   # Flask-Wrapper + Piper HTTP-Server
├── system.md          # Setup-Anleitung
├── requirements.txt   # Python-Abhängigkeiten
├── models/
│   ├── de_DE-thorsten-high.onnx       # 109 MB Voice-Modell
│   └── de_DE-thorsten-high.onnx.json  # Modell-Metadata
└── README.md
```

## License

MIT
