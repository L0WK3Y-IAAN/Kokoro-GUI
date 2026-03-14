# Kokoro-GUI

A local (or cloud-hosted) web interface for **Kokoro TTS** (text-to-speech). It runs a Flask API that uses the [Kokoro](https://github.com/hexgrad/kokoro) model to synthesize speech, plus a single-page dark-themed UI to pick languages/voices, enter text, adjust speed and pitch, and play or download WAV output.

## Features

- **Multi-language voices** — American English, British English, French, Italian, Japanese, Spanish, Mandarin Chinese, Hindi, Brazilian Portuguese (Kokoro v1.0 voice set).
- **Region + voice selector** — Choose a language/region, then pick a voice from that region.
- **Playback speed** — Slider from 0.5× to 3× (sent to the API).
- **Pitch adjustment** — Client-side pitch shift (0.5×–2×) with no change to synthesis; higher pitch shortens duration, lower lengthens it.
- **Download** — Save the current audio (including pitch) as a WAV; filename is derived from the first part of the text (e.g. `Hello! This is a test....wav`).
- **Optional GitHub Pages UI** — Deploy the static UI to GitHub Pages and run the API locally or via a GitHub Actions + localtunnel workflow.

## Requirements

- **Python 3.12** (required; 3.13+ breaks Kokoro/spacy due to Pydantic v1).
- [uv](https://github.com/astral-sh/uv) (installed automatically by the setup script if missing).
- Enough disk and RAM for the Kokoro model and PyTorch/torchaudio.

## Quick start

1. Clone the repo and enter the project folder:
   ```bash
   cd Kokoro-GUI
   ```

2. Run the setup script (creates a venv, installs dependencies, then starts the server):
   ```bash
   python setup.py
   ```

3. Open **`index.html`** in your browser (or the script may open `web_gui.html` if present). The page talks to the API at `http://127.0.0.1:8000`.

4. Select a region and voice, enter text, set speed (and optionally pitch), then **Generate Speech**. Use **Download Audio** to save the WAV.

The Flask backend runs at **http://127.0.0.1:8000** and lazy-loads Kokoro pipelines per language on first use.

## Manual setup (optional)

If you prefer to manage the environment yourself:

1. Create and activate a virtual environment (Python 3.12):
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   # .venv\Scripts\activate    # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the API server:
   ```bash
   python api_server.py
   ```

4. Open **`index.html`** in a browser.

## GitHub Pages and cloud API

- **Deploy UI to GitHub Pages**  
  The workflow in `.github/workflows/deploy-pages.yml` runs on push to `main` and deploys the repo (including `index.html`) to GitHub Pages. Enable Pages in the repo **Settings → Pages** with source **GitHub Actions**. The live site will try to reach the API at `http://127.0.0.1:8000`; use it from the same machine where the API is running, or change `API_BASE` in `index.html` to point to your server.

- **Run API in the cloud (Actions + localtunnel)**  
  The workflow in `.github/workflows/run-api.yml` can be triggered manually (**Actions → Host Kokoro API Server → Run workflow**). It starts the API on an Ubuntu runner, exposes it with [localtunnel](https://localtunnel.github.io/www/), and prints a public URL. Paste that URL into `API_BASE` in `index.html` (or use it as the API URL in the UI if you add an API URL field) so the GitHub Pages UI can talk to the cloud API.

## Project layout

| File / folder              | Purpose |
|----------------------------|--------|
| `index.html`               | Main web UI: region/voice, text, speed, pitch, generate, download WAV |
| `api_server.py`            | Flask app: `GET /voices` (regions + voices), `POST /synthesize`; lazy-loads Kokoro pipelines by language |
| `setup.py`                 | One-shot setup: ensures uv, creates `.venv` (Python 3.12), installs deps, starts the server, optionally opens the GUI |
| `requirements.txt`         | Python dependencies (Flask, flask-cors, kokoro, soundfile, torch, torchaudio) |
| `sample_generate.py`       | Minimal CLI example of Kokoro usage (no server) |
| `.github/workflows/deploy-pages.yml` | Deploys the repo to GitHub Pages (static UI) |
| `.github/workflows/run-api.yml`      | Manual workflow to run the API on a runner and expose it via localtunnel |

## API

- **`GET /voices`** — Returns `{ "regions": { "American English": ["af_heart", ...], "British English": [...], ... } }`. Pipelines are loaded on demand by language code (first character of voice ID).
- **`POST /synthesize`** — Body: `{ "text": "...", "voice": "af_heart", "speed": 1.0 }`. Returns a WAV file (24 kHz).

## Voices

The server exposes Kokoro v1.0 voices grouped by region: American English, British English, French, Italian, Japanese, Spanish, Mandarin Chinese, Hindi, and Brazilian Portuguese. The UI loads regions from `/voices`, then lets you pick a region and a voice from that list. The default region is American English.

## Notes

- First run will download the Kokoro model; later runs use the cached copy.
- The setup script uses **uv** for fast, reliable installs and will install uv via the official installer or pip if it’s not found.
- **Python 3.12** is required; the script creates a 3.12 venv and will warn if an existing `.venv` is not 3.12.
