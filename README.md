# DubFlow AI — AI-Powered Video Dubbing SaaS Platform

DubFlow AI is a complete, enterprise-grade AI-powered video dubbing SaaS platform. It allows users to upload a video, automatically analyze every speaker, transcribe dialogue with timestamps, translate it into another language using NVIDIA AI, generate distinct AI voices for each speaker, synchronize speech with original timing, preserve background music/SFX, and reconstruct the final dubbed video.

---

## Key Features

1. **Automatic Speaker Diarization & Voice Profiling**:
   - Detects all speakers without prior count assumptions.
   - Extracts 108-dimensional normalized acoustic embeddings (MFCCs, spectral contrast, pitch F0 contour, energy).
   - Computes vocal characteristics (pitch, speaking rate, loudness, gender).
   - Generates audio sample previews for every speaker.
   - Allows renaming speakers (e.g. "Speaker 01" &rarr; "John") and reassigning AI voices.

2. **Accurate Speech-to-Text (ASR)**:
   - OpenAI Whisper integration with millisecond-precision timestamps and confidence scoring.
   - Aligns every sentence and word to the correct speaker.

3. **Context-Aware LLM Translation (NVIDIA Cloud API)**:
   - Powered by NVIDIA AI (`nvidia/riva-translate-4b-instruct-v2` via NVIDIA Integrate API).
   - Contextual dialogue awareness (previous/following lines, character persona, timing duration hints).
   - Supports French, Spanish, Arabic, German, Turkish, Portuguese, Italian, English, and more.

4. **Multi-Speaker Neural TTS**:
   - Distinct AI voices per speaker; speaker identity remains consistent throughout the video.
   - Neural voice catalog with male/female options and native accents.

5. **Broadcast Timing Synchronization**:
   - Compares synthesized speech duration against original speech duration.
   - Applies intelligent time stretching (`atempo` / `librubberband`) within natural limits (0.85x – 1.25x).
   - Inserts natural silence padding or trims excess pauses so dubbing aligns with video lips and scenes.

6. **Soundtrack & SFX Preservation**:
   - Dialogue suppression/ducking during speech timestamps.
   - Full fidelity preservation of background music, ambient noise, and sound effects outside speech.
   - Configurable Dialogue Volume, Music Volume, and Voice Suppression sliders.

7. **Lossless Video Reconstruction**:
   - Preserves original video stream quality, framerate, and resolution using FFmpeg stream copying (`-c:v copy`) and AAC stereo audio muxing (`-c:a aac -b:a 192k`).

8. **GPU Memory Lifecycle Management (RTX A2000 4GB VRAM)**:
   - Dynamic model loading & unloading with `torch.cuda.empty_cache()` and `gc.collect()`.
   - Batch size 1, FP16 execution, and CPU fallback.
   - Heavy translation offloaded to NVIDIA Cloud API.

9. **Live Diagnostic Engine ("Run Test")**:
   - Verifies FFmpeg, PyTorch, CUDA, NVIDIA API, Whisper ASR, Diarization, and TTS with live status indicators.

---

## Technology Stack

- **Backend**: Python 3.12, FastAPI, PyTorch, FFmpeg, OpenCV, NumPy, Librosa, SoundFile, Scikit-learn, WebSockets.
- **Frontend**: Single-Page Application (HTML5, Vanilla JavaScript, Tailwind CSS via CDN, Lucide Icons, Glassmorphism design).
- **Database**: SQLite (SQLAlchemy ORM, structured for easy drop-in replacement with PostgreSQL).
- **AI Models & APIs**:
  - Whisper ASR (local, VRAM-managed)
  - Acoustic Feature Diarization (Librosa + Agglomerative Cosine Clustering)
  - NVIDIA Cloud Translation API (`nvidia/riva-translate-4b-instruct-v2`)
  - Edge-TTS Neural Studio Voices

---

## Directory Structure

```
dubflow ai/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint, CORS, static routes
│   │   ├── api/
│   │   │   ├── projects.py             # Project CRUD & video upload
│   │   │   ├── dubbing.py              # Analyze, dub, and export endpoints
│   │   │   ├── speakers.py             # Speaker profiles, rename, voice preview
│   │   │   ├── transcript.py           # Transcript query, edit, line regeneration
│   │   │   ├── jobs.py                 # Job polling & WebSocket updates
│   │   │   ├── diagnostics.py          # "Run Test" system health verification
│   │   │   ├── languages.py            # Language and voice catalog
│   │   │   └── media.py                # Media streaming with range requests
│   │   ├── core/
│   │   │   ├── config.py               # Settings & storage directories
│   │   │   ├── logging.py              # Structured stage logging ([ASR], [TTS], etc.)
│   │   │   └── database.py             # SQLAlchemy session & SQLite database
│   │   ├── models/
│   │   │   ├── project.py              # Project entity
│   │   │   ├── speaker.py              # Speaker profile entity
│   │   │   ├── transcript.py           # Dialogue line entity
│   │   │   └── job.py                  # Background job & log entity
│   │   ├── services/
│   │   │   ├── video_service.py        # Video inspection & metadata
│   │   │   ├── audio_service.py        # Audio extraction & preprocessing
│   │   │   ├── asr_service.py          # Whisper transcription
│   │   │   ├── diarization_service.py  # Diarization & speaker alignment
│   │   │   ├── speaker_service.py      # Voice characteristics & sample extraction
│   │   │   ├── translation_service.py  # Contextual NVIDIA translation
│   │   │   ├── tts_service.py          # Neural voice synthesis
│   │   │   ├── synchronization_service.py # Audio time stretching & padding
│   │   │   ├── mixing_service.py       # Audio mixing & vocal suppression
│   │   │   ├── rendering_service.py    # Final video muxing
│   │   │   └── language_service.py     # LanguageManager catalog
│   │   ├── providers/
│   │   │   ├── base.py                 # Abstract base classes
│   │   │   ├── nvidia/                 # NVIDIA Cloud adapters
│   │   │   └── local/                  # Local Whisper, Diarization, Edge-TTS
│   │   ├── workers/
│   │   │   └── dubbing_worker.py       # Asynchronous background pipeline orchestrator
│   │   └── utils/
│   │       ├── ffmpeg.py               # FFmpeg wrapper & ffprobe
│   │       ├── audio.py                # Acoustic feature analysis
│   │       ├── gpu.py                  # VRAM tracking & garbage collection
│   │       └── timestamps.py           # Timestamp formatting helpers
│   ├── storage/
│   │   ├── uploads/                    # Uploaded video files
│   │   ├── audio/                      # Extracted stems & master audio
│   │   ├── segments/                   # Individual dialogue line WAVs
│   │   ├── voices/                     # Speaker profile sample clips
│   │   ├── outputs/                    # Final dubbed MP4 videos
│   │   └── projects/                   # Project backups
│   └── requirements.txt
├── frontend/
│   ├── index.html                      # Single-page SaaS interface
│   ├── app.js                          # State controller, WebSockets & UI
│   └── styles.css                      # Custom dark mode styles
├── .env                                # Active environment configuration
├── .env.example
└── README.md
```

---

## Quick Start & Running Locally

1. **Activate Environment & Check Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Configure `.env`**:
   Verify `NVIDIA_API_KEY` is present:
   ```ini
   NVIDIA_API_KEY=nvapi-...
   ```

3. **Start the DubFlow AI Server**:
   ```bash
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Open in Browser**:
   Navigate to:
   ```
   http://127.0.0.1:8000
   ```

5. **Run Diagnostics**:
   Click **"System Health"** in the top navigation bar to verify all AI components and hardware acceleration.

---

## SaaS Production Roadmap

The codebase is structured to scale smoothly into a multi-tenant cloud platform:
- **Database**: Replace `DATABASE_URL=sqlite:///./storage/dubflow.db` with `postgresql://user:pass@host:5432/dubflow` in `.env`.
- **Job Queues**: Replace in-process `dubbing_worker` with Celery or Temporal backed by Redis/RabbitMQ.
- **Storage**: Swap local `/storage` paths with Amazon S3 / Cloudflare R2 / Google Cloud Storage.
- **Worker Clusters**: Deploy stateless GPU worker nodes with auto-scaling based on queue depth.