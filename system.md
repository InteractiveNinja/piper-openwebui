# Piper TTS Bridge — System-Setup

## Quick-Start

```bash
# API-Key setzen
export PIPER_ENV_KEY="dein_geheimer_key"

# Wrapper starten
python piper-wrapper.py
```

## Open WebUI-Konfiguration

In Open WebUI unter **Settings → Audio → Text-to-Speech**:

| Feld | Wert |
|------|------|
| Provider | `Custom` |
| URL | `http://localhost:8082/audio/speech` |
| API-Key | `dein_geheimer_key` |
| Model | `de_DE-thorsten-high` |

## Voice-Model

Das Modell `de_DE-thorsten-high.onnx` (109 MB) liegt lokal im `models/`-Ordner.
Es wird automatisch vom Wrapper geladen.

## Port-Übersicht

| Dienst | Port |
|--------|------|
| Piper TTS HTTP | 8083 |
| Wrapper (Open WebUI Bridge) | 8082 |

## API-Key

Der Key wird über die Umgebungsvariable `PIPER_ENV_KEY` gelesen.
Beispiel für systemd / Docker:

```bash
export PIPER_ENV_KEY="mein_sicherer_key"
```

Keine `.api-key`-Datei mehr nötig — alles über Environment.

## Test

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dein_geheimer_key" \
  -d '{"text": "Hallo Welt"}' \
  http://127.0.0.1:8082/audio/speech -o test.wav
```

→ sollte WAV-Datei zurückgeben.