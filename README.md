# Piper TTS Bridge für Open WebUI

> ⚠️ **Hinweis:** Dieser Code wurde vollständig von einer KI generiert und nicht manuell geprüft.
> Nutze ihn auf eigene Gefahr und prüfe kritische Stellen (Auth, Network, TTS-Qualität) vor Produktiveinsatz.

Ein kleiner Flask-Wrapper, der Open WebUIs TTS-Endpunkt (`/audio/speech`) an einen lokalen Piper TTS-Server weiterleitet.

## Features

- **API-Endpunkt:** `POST /audio/speech` (Open WebUI Standard)
- **Piper HTTP-Server:** Läuft auf Port 8083, antwortet auf `/synthesize`
- **Stimmen-Auswahl:** `voice`-Parameter wählt `models/{voice}.onnx`
- **API-Key-Auth:** Über Umgebungsvariable `PIPER_ENV_KEY`
- **GPU-Beschleunigung:** Optional via `USE_GPU=1` (NVIDIA CUDA / AMD ROCm)
- **Graceful Shutdown:** Piper wird bei `Ctrl+C` sauber beendet

## Setup

```bash
# Virtual Environment
python -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt

# GPU-Beschleunigung (optional)
# pip install onnxruntime-rocm   # AMD
# pip install onnxruntime-gpu    # NVIDIA

# API-Key setzen
export PIPER_ENV_KEY="dein_geheimer_key"

# Wrapper starten
python piper-wrapper.py

# Wrapper mit GPU starten
USE_GPU=1 python piper-wrapper.py
```

## Open WebUI-Konfiguration

Unter **Settings → Audio → Text-to-Speech**:

| Feld | Wert |
|------|------|
| Provider | `Custom` |
| URL | `http://localhost:8082/audio/speech` |
| API-Key | `dein_geheimer_key` (als `Authorization: Bearer ...`) |
| Model | `de_DE-thorsten-high` |

## Port-Übersicht

| Dienst | Port |
|--------|------|
| Piper TTS HTTP | 8083 |
| Wrapper (Open WebUI Bridge) | 8082 |

## Stimmen-Auswahl

Legen Sie `.onnx`-Modelle direkt in `models/` ab:

```bash
ls models/*.onnx
# models/alloy.onnx  models/de_DE-thorsten-high.onnx
```

Die Stimme wird über das `voice`-Feld gewählt:

```bash
curl -X POST \
  -H "Authorization: Bearer dein_geheimer_key" \
  -d '{"voice": "alloy", "input": "Hallo Welt"}' \
  http://127.0.0.1:8082/audio/speech -o alloy.wav
```

Kein `voice`-Feld → Default-Modell (`de_DE-thorsten-high.onnx`).
Unbekannte Stimme → `400`.

## Test

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dein_geheimer_key" \
  -d '{"input": "Hallo Welt"}' \
  http://127.0.0.1:8082/audio/speech -o test.wav
```

## GPU-Beschleunigung

Um die Synthese auf einer AMD- oder NVIDIA-GPU auszuführen:

```bash
USE_GPU=1 python piper-wrapper.py
```

Voraussetzungen für AMD ROCm:
- `onnxruntime-rocm` installiert
- `libhipblas.so.3` verfügbar (ggf. manuell nachinstallieren)

Voraussetzungen für NVIDIA CUDA:
- `onnxruntime-gpu` installiert
- CUDA Toolkit / NVIDIA Treiber

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
