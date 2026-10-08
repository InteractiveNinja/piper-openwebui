# Anforderung: Piper TTS Bridge für Open WebUI

## Ziel

Eine Python-Flask-App (`piper-wrapper.py`), die `/audio/speech` → `/synthesize` mappt, Piper automatisch startet und API-Key-Auth bietet.

## Anforderungen an den Coding Agent

### 1. Datei: `piper-wrapper.py`

Erstelle eine Flask-App mit folgenden Features:

*   **API-Endpunkt:** `POST /audio/speech` (Open WebUI Standard)
    
*   **Forwarding:** POST-Body an `http://127.0.0.1:8080/synthesize` (Piper native)
    
*   **Auth:** Header `X-API-Key` prüfen. Key aus `/opt/piper/.api-key` lesen (falls `API_KEY=""`).
    
*   **Piper starten:** `piper.http_server` als `subprocess` auf Port 8080, Modell `models/de_DE-thorsten-high.onnx`.
    
*   **Warten:** Bis Piper auf `/info` antwortet (max. 10s).
    
*   **Shutdown:** Graceful termination von Piper bei `Ctrl+C`.
    
*   **Konfiguration:** Variablen am Dateianfang: `HOST`, `PORT`, `PIPER_HOST`, `PIPER_PORT`, `PIPER_MODEL`, `API_KEY`.
    

### 2. Datei: `system.md`

Erstelle eine Markdown-Datei mit:

*   Setup-Anleitung (API-Key setzen, Wrapper starten)
    
*   Open WebUI-Konfiguration (TTS Provider, URL, API-Key)
    
*   Port-Übersicht (Piper 8080, Wrapper 8082)
    
*   Hinweis auf API-Key-Datei `/opt/piper/.api-key`
    

### 3. Datei: `.api-key`

Leere Datei erstellen (oder Template: `echo "dein_geheimer_key" > .api-key`).

## Test

Der Agent soll nach der Installation prüfen:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "Hallo Welt"}' \
  http://127.0.0.1:8082/audio/speech -o test.wav
```

→ sollte WAV-Datei zurückgeben.

## Hinweis

Der Wrapper soll **kein** `docker-compose` erstellen – das läuft separat auf dem Remote-Server `llama`. Nur die Bridge-Dateien hier lokal.