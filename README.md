# Interview Translator (EN→ES) con Preservación de Voz

Herramienta offline batch que toma entrevistas en inglés y produce:
- Transcripción en español por hablante con timestamps
- Audio doblado al español con clonación de voz (voz similar al original)
- Archivo de audio final mezclado (WAV + MP3)

## Pipeline

1. **ASR**: WhisperX — transcripción + alineación word-level
2. **Diarización**: pyannote.audio Community-1 — detección de hablantes
3. **Merge**: Asignación de texto a hablantes por overlap temporal
4. **Traducción**: NLLB-200 distilled 600M (EN→ES)
5. **TTS**: Coqui XTTS v2 — generación de audio español con voz clonada
6. **Render**: Stitching en timeline + export WAV/MP3

## Requisitos

- Python 3.10+
- ffmpeg instalado y en PATH
- Apple Silicon (MPS para traducción, CPU para el resto) o GPU CUDA
- Token de Hugging Face (para modelos pyannote)

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crear archivo `.env` con tu token de Hugging Face:
```bash
cp .env.example .env
# Editar .env con tu HF_TOKEN
```

## Uso

```bash
python -m src.main \
  --input data/input/interview.mp3 \
  --workdir data/work/interview \
  --max-speakers 2
```

### Opciones

- `--input`: Archivo de audio de entrada (.mp3 o .wav)
- `--workdir`: Directorio de trabajo para outputs intermedios
- `--config`: Archivo de configuración YAML (default: configs/default.yaml)
- `--max-speakers`: Número máximo de hablantes (default: 2)
- `--force`: Re-ejecutar todos los pasos aunque ya existan outputs
- `--steps`: Ejecutar solo pasos específicos (ej: `--steps asr diarize`)

## Outputs

| Archivo | Descripción |
|---|---|
| `asr.json` | Transcripción con timestamps word-level |
| `diarization.rttm` | Turnos de hablante (formato RTTM) |
| `merged_segments.json` | Segmentos con speaker + texto EN + texto ES |
| `translations.json` | Traducciones EN→ES por segmento |
| `tts_segments/` | Audio TTS generado por segmento/hablante |
| `rendered.wav` | Audio final en español |
| `rendered.mp3` | Export MP3 del audio final |

## Licencias de modelos

- Whisper / WhisperX: MIT
- pyannote.audio: MIT (modelo requiere aceptar condiciones en HF)
- NLLB-200: CC-BY-NC-4.0
- Coqui XTTS v2: CPML
