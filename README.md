<p align="center">
  <img src="frontend/public/logo.png" alt="Loro" width="180" />
</p>

<h1 align="center">Loro</h1>
<p align="center"><strong>Traductor de Entrevistas (EN→ES) con Preservacion de Voz</strong></p>

Herramienta offline batch que toma entrevistas en ingles y produce:
- Transcripcion en espanol por hablante con timestamps
- Audio doblado al espanol con clonacion de voz (voz similar al original)
- Archivo de audio final mezclado (WAV + MP3)

Incluye una **interfaz web** (FastAPI + Next.js) para subir audio o pegar un link de YouTube, ver progreso en tiempo real y reproducir la entrevista traducida con switch instantaneo de idioma EN/ES.

---

## Tabla de contenidos

- [Arquitectura](#arquitectura)
- [Pipeline completo](#pipeline-completo)
- [Librerias y modelos](#librerias-y-modelos)
- [Requisitos del sistema](#requisitos-del-sistema)
- [Instalacion](#instalacion)
- [Configuracion](#configuracion)
- [Uso via CLI](#uso-via-cli)
- [Uso via Web](#uso-via-web)
- [API endpoints](#api-endpoints)
- [Outputs](#outputs)
- [Licencias de modelos](#licencias-de-modelos)
- [Licencia del proyecto](#licencia-del-proyecto)

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                   │
│  Upload / YouTube URL → Progreso en tiempo real → Player │
└────────────────────────┬────────────────────────────────┘
                         │ REST + WebSocket
┌────────────────────────▼────────────────────────────────┐
│                   Backend (FastAPI)                       │
│  /api/jobs (CRUD) · /api/jobs/youtube · /api/jobs/{id}/ws│
└────────────────────────┬────────────────────────────────┘
                         │ progress_callback
┌────────────────────────▼────────────────────────────────┐
│                  Pipeline (Python)                        │
│  [Download] → ASR → Diarize → Merge → Translate → TTS → Render │
└─────────────────────────────────────────────────────────┘
```

El pipeline funciona de forma independiente via CLI o a traves del backend web. Ambos modos comparten el mismo codigo de pipeline.

---

## Pipeline completo

### 1. ASR (Automatic Speech Recognition)

**Motor**: WhisperX (basado en faster-whisper)

Transcribe el audio de ingles a texto con timestamps a nivel de palabra. WhisperX usa CTranslate2 como backend, lo que lo hace significativamente mas rapido que el Whisper original de OpenAI. Ademas provee alineacion forzada (forced alignment) para obtener timestamps precisos por palabra.

- **Entrada**: archivo de audio (.mp3 o .wav)
- **Salida**: `asr.json` con segmentos de texto + timestamps word-level
- **Modelo**: `large-v2` (configurable)

### 2. Diarizacion (Speaker Diarization)

**Motor**: pyannote.audio con modelo Community-1

Detecta "quien hablo cuando" en el audio. Genera turnos de hablante con timestamps de inicio y fin. Usa un modelo neural entrenado para segmentacion y clustering de hablantes.

- **Entrada**: archivo de audio original
- **Salida**: `diarization.rttm` (formato estandar RTTM)
- **Modelo**: `pyannote/speaker-diarization-3.1`
- **Nota**: requiere token de Hugging Face y aceptar condiciones del modelo

### 3. Merge (Fusion ASR + Diarizacion)

Combina la transcripcion (ASR) con la diarizacion para asignar cada segmento de texto a un hablante especifico. El algoritmo calcula el overlap temporal entre cada segmento de ASR y los turnos de diarizacion, asignando el hablante con mayor superposicion.

- **Entrada**: `asr.json` + `diarization.rttm`
- **Salida**: `merged_segments.json` (segmentos con speaker_id + texto EN)
- **Post-procesamiento**: filtro de mediana para suavizar cambios rapidos de hablante, merge de segmentos muy cortos (<0.5s)

### 4. Traduccion (EN→ES)

**Motor**: NLLB-200 (No Language Left Behind)

Traduce cada segmento de ingles a espanol preservando la estructura de turnos. Usa el modelo distilado de 600M de parametros, que ofrece buen balance entre calidad y velocidad.

- **Entrada**: `merged_segments.json`
- **Salida**: `translations.json` (segmentos con text_en + text_es + speaker + timestamps)
- **Modelo**: `facebook/nllb-200-distilled-600M`
- **Batch size**: 8 segmentos (configurable)

### 5. TTS (Text-to-Speech con clonacion de voz)

**Motor**: Coqui XTTS v2

Genera audio en espanol para cada segmento usando clonacion de voz. Para cada hablante, se extrae automaticamente un clip de referencia del audio original (6-30s de habla limpia) y XTTS v2 genera el audio en espanol imitando esa voz.

- **Entrada**: `translations.json` + audio original (para clips de referencia)
- **Salida**: `tts_segments/SPEAKER_XX/seg_NNNN.wav` (un archivo por segmento)
- **Modelo**: `tts_models/multilingual/multi-dataset/xtts_v2`
- **Cache**: los segmentos TTS se cachean por hash de texto para evitar regeneracion

### 6. Render (Mezcla final)

Ensambla todos los segmentos TTS en una linea de tiempo independiente para el espanol. Aplica time-stretching suave (limites: 0.85x a 1.15x) y coloca los segmentos secuencialmente preservando los gaps originales. Normaliza el volumen a -16 LUFS y aplica crossfade entre segmentos. Genera un mapa de correspondencia entre las lineas de tiempo EN y ES.

- **Entrada**: `tts_segments/` + `translations.json`
- **Salida**: `rendered.wav` + `rendered.mp3` + `timeline_map.json`
- **Sample rate**: 44100 Hz (resampleado desde 22050 Hz nativo de XTTS)
- **MP3**: ~190kbps VBR via ffmpeg

---

## Librerias y modelos

### Procesamiento de audio y ML

| Libreria | Version | Descripcion |
|----------|---------|-------------|
| **WhisperX** | >=3.1.1 | ASR con alineacion word-level. Usa faster-whisper (CTranslate2) como backend para transcripcion rapida y eficiente |
| **pyannote.audio** | >=3.1 | Toolkit de diarizacion de hablantes. Modelo neural para detectar y separar voces en audio multi-hablante |
| **transformers** | >=4.36.0 | Hugging Face Transformers. Provee la infraestructura para cargar y ejecutar el modelo de traduccion NLLB-200 |
| **sentencepiece** | >=0.1.99 | Tokenizador sub-word requerido por NLLB-200 para procesar texto en multiples idiomas |
| **accelerate** | >=0.25.0 | Optimiza la carga y ejecucion de modelos en diferentes dispositivos (CPU, MPS, CUDA) |
| **TTS** | >=0.22.0 | Coqui TTS toolkit. Incluye XTTS v2 para sintesis de voz multilingue con clonacion de voz a partir de clips de referencia |
| **torch** | >=2.1.0 | PyTorch. Framework de deep learning base para todos los modelos del pipeline |
| **torchaudio** | >=2.1.0 | Extension de PyTorch para procesamiento de audio (carga, transformaciones, resampleo) |

### Procesamiento de audio

| Libreria | Version | Descripcion |
|----------|---------|-------------|
| **pydub** | >=0.25.1 | Manipulacion de audio de alto nivel (cortar, concatenar, convertir formatos). Usa ffmpeg como backend |
| **soundfile** | >=0.12.1 | Lectura/escritura de archivos de audio (WAV, FLAC) basado en libsndfile |
| **librosa** | >=0.10.1 | Analisis de audio y musica. Usado para resampleo y carga de audio |
| **numpy** | >=1.24.0 | Computacion numerica. Manipulacion de arrays de audio como datos numericos |
| **pyloudnorm** | >=0.1.1 | Normalizacion de volumen segun estandar ITU-R BS.1770 (medicion y ajuste de LUFS) |

### CLI y configuracion

| Libreria | Version | Descripcion |
|----------|---------|-------------|
| **click** | >=8.1.0 | Framework para crear CLIs en Python. Manejo de argumentos y opciones |
| **pyyaml** | >=6.0.1 | Parser YAML para leer archivos de configuracion del pipeline |
| **rich** | >=13.7.0 | Terminal output enriquecido. Progress bars, colores y formato de logs |
| **python-dotenv** | >=1.0.0 | Carga variables de entorno desde archivo `.env` (ej: HF_TOKEN) |

### Descarga de YouTube

| Libreria | Version | Descripcion |
|----------|---------|-------------|
| **yt-dlp** | >=2024.1.0 | Fork activo de youtube-dl. Descarga audio de YouTube y lo convierte a WAV via ffmpeg |

### Backend web (FastAPI)

| Libreria | Version | Descripcion |
|----------|---------|-------------|
| **FastAPI** | >=0.109.0 | Framework web asincrono de alto rendimiento. Provee la API REST y WebSocket para la interfaz web |
| **uvicorn** | >=0.25.0 | Servidor ASGI para ejecutar la aplicacion FastAPI. Soporta hot-reload en desarrollo |
| **python-multipart** | >=0.0.6 | Parsing de formularios multipart/form-data. Necesario para upload de archivos via la API |
| **websockets** | >=12.0 | Implementacion WebSocket para Python. Usado para enviar progreso del pipeline en tiempo real |

### Frontend (Next.js)

| Libreria | Version | Descripcion |
|----------|---------|-------------|
| **Next.js** | 16.x | Framework React con App Router, server components y file-based routing |
| **React** | 19.x | Libreria UI. Usa hooks y concurrent features |
| **SWR** | >=2.4.0 | Data fetching con cache, revalidacion automatica y polling. Maneja el estado de jobs y segmentos |
| **Tailwind CSS** | v4 | Framework CSS utility-first para estilos de la interfaz |
| **shadcn/ui** | 3.x | Componentes UI reutilizables (Card, Badge, Button, Progress, Slider) basados en Radix UI |
| **Radix UI** | 1.x | Primitivos UI accesibles y sin estilos. Base de los componentes shadcn |

---

## Requisitos del sistema

- **Python** 3.10+
- **Node.js** 18+ y npm (para el frontend)
- **ffmpeg** instalado y en PATH
- **Apple Silicon** (MPS para traduccion, CPU para el resto) o **GPU CUDA**
- **Token de Hugging Face** (para modelos pyannote) — [crear cuenta](https://huggingface.co/join)
- ~8 GB de espacio para modelos (se descargan en la primera ejecucion)

---

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/apps-ark/Loro.git
cd Loro
```

### 2. Backend (Python)

```bash
# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y agregar tu token de Hugging Face:

```
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> Para obtener el token: ir a [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) y crear un token con permisos de lectura. Ademas, aceptar las condiciones del modelo pyannote en [huggingface.co/pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1).

### 4. Frontend (Next.js)

```bash
cd frontend
npm install
```

El frontend ya viene configurado para conectarse al backend en `http://localhost:8000` via el archivo `.env.local`.

---

## Configuracion

La configuracion del pipeline esta en `configs/default.yaml`. Los parametros principales:

| Seccion | Parametro | Default | Descripcion |
|---------|-----------|---------|-------------|
| asr | model_size | large-v2 | Tamano del modelo Whisper |
| asr | compute_type | float32 | Tipo de computacion (float32 para CPU/MPS) |
| diarization | max_speakers | 2 | Numero maximo de hablantes a detectar |
| translation | batch_size | 8 | Segmentos por batch de traduccion |
| tts | ref_min_duration | 6.0 | Duracion minima del clip de referencia (segundos) |
| tts | ref_max_duration | 30.0 | Duracion maxima del clip de referencia (segundos) |
| render | stretch_min | 0.85 | Time-stretch minimo permitido |
| render | stretch_max | 1.15 | Time-stretch maximo permitido |
| render | target_lufs | -16.0 | Nivel de normalizacion de volumen |

---

## Uso via CLI

```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar pipeline completo
python -m src.main \
  --input data/input/interview.mp3 \
  --workdir data/work/interview \
  --max-speakers 2
```

### Opciones del CLI

| Opcion | Descripcion |
|--------|-------------|
| `--input` | Archivo de audio de entrada (.mp3 o .wav) |
| `--workdir` | Directorio de trabajo para outputs intermedios |
| `--config` | Archivo de configuracion YAML (default: `configs/default.yaml`) |
| `--max-speakers` | Numero maximo de hablantes (default: 2) |
| `--force` | Re-ejecutar todos los pasos aunque ya existan outputs |
| `--steps` | Ejecutar solo pasos especificos (ej: `--steps asr diarize`) |

### Ejecucion por pasos

```bash
# Solo transcripcion y diarizacion
python -m src.main --input audio.mp3 --workdir work/ --steps asr diarize

# Solo traduccion (requiere merge previo)
python -m src.main --input audio.mp3 --workdir work/ --steps translate

# Re-ejecutar TTS forzando regeneracion
python -m src.main --input audio.mp3 --workdir work/ --steps tts --force
```

---

## Uso via Web

### Levantar el backend

```bash
# En la raiz del proyecto, con el venv activado
source .venv/bin/activate
uvicorn src.api.app:app --reload --port 8000
```

El backend estara disponible en `http://localhost:8000`.

### Levantar el frontend

```bash
# En otra terminal
cd frontend
npm run dev
```

El frontend estara disponible en `http://localhost:3000`.

### Flujo de uso en la web

1. **Subir audio o pegar URL de YouTube**: la interfaz ofrece dos tabs:
   - **Subir archivo**: arrastrar o seleccionar un archivo .mp3/.wav
   - **URL de YouTube**: pegar un link de YouTube (se descarga el audio automaticamente)
2. **Configurar**: seleccionar numero maximo de hablantes (default: 2)
3. **Procesar**: click en "Traducir Entrevista" — el pipeline se ejecuta en background
4. **Monitorear progreso**: la vista de procesamiento muestra cada paso del pipeline en tiempo real via WebSocket. Para URLs de YouTube se agrega un paso previo "Descargando audio de YouTube" con barra de progreso
5. **Reproducir**: cuando completa, el player permite:
   - Reproducir audio original (EN) o traducido (ES)
   - Cambiar idioma instantaneamente (sin pausa)
   - Ver subtitulos sincronizados por hablante
   - Click en un subtitulo para saltar a esa posicion
   - Atajos de teclado: Espacio (play/pause), L (cambiar idioma), flechas (seek)
6. **Reintentar**: si un job falla, se puede reintentar desde la lista de trabajos sin necesidad de volver a subir el archivo

---

## API endpoints

### REST

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `POST` | `/api/jobs` | Upload audio (multipart: file, max_speakers) → 201 |
| `POST` | `/api/jobs/youtube` | Crear job desde URL de YouTube (JSON: url, max_speakers) → 201 |
| `GET` | `/api/jobs` | Lista de todos los jobs |
| `GET` | `/api/jobs/{id}` | Detalle de un job |
| `POST` | `/api/jobs/{id}/retry` | Reintentar un job fallido |
| `DELETE` | `/api/jobs/{id}` | Eliminar job y archivos asociados |
| `GET` | `/api/jobs/{id}/audio/original` | Stream audio EN (soporta Range headers) |
| `GET` | `/api/jobs/{id}/audio/translated` | Stream audio ES (soporta Range headers) |
| `GET` | `/api/jobs/{id}/segments` | Segmentos con text_en, text_es, speaker, timestamps |
| `GET` | `/api/health` | Health check |

### WebSocket

| Ruta | Descripcion |
|------|-------------|
| `WS /api/jobs/{id}/ws` | Progreso en tiempo real del pipeline |

Mensajes WebSocket (server→client):

```json
{"type": "step_start", "step": "asr"}
{"type": "step_progress", "step": "translate", "current": 5, "total": 22}
{"type": "step_complete", "step": "translate"}
{"type": "pipeline_complete"}
{"type": "error", "step": "tts", "message": "..."}
```

---

## Outputs

| Archivo | Descripcion |
|---------|-------------|
| `asr.json` | Transcripcion con timestamps word-level |
| `diarization.rttm` | Turnos de hablante (formato RTTM estandar) |
| `merged_segments.json` | Segmentos con speaker + texto EN |
| `translations.json` | Traducciones EN→ES por segmento con timestamps |
| `tts_segments/` | Audio TTS generado por segmento y hablante |
| `rendered.wav` | Audio final en espanol (lossless) |
| `rendered.mp3` | Export MP3 del audio final (~190kbps VBR) |
| `timeline_map.json` | Mapa de correspondencia de timestamps entre timelines EN y ES |

---

## Licencias de modelos

| Modelo | Licencia |
|--------|----------|
| Whisper / WhisperX | MIT |
| faster-whisper | MIT |
| pyannote.audio | MIT (modelo requiere aceptar condiciones en HF) |
| NLLB-200 distilled | CC-BY-NC-4.0 |
| Coqui XTTS v2 | CPML (Coqui Public Model License) |

> **Nota**: NLLB-200 tiene licencia NC (no comercial). Si necesitas uso comercial, considera usar un modelo de traduccion alternativo.

---

## Licencia del proyecto

Este proyecto esta licenciado bajo la [Licencia MIT](LICENSE).
