# Kokoro-GUI

A local web interface for **Kokoro TTS** (text-to-speech). It runs a Flask API that uses the [Kokoro](https://github.com/hexgrad/kokoro) model to synthesize speech, plus a single-page dark-themed UI to pick voices, enter text, and play or download WAV output.

## Requirements

- **Python 3.13** (tested and working)
- [uv](https://github.com/astral-sh/uv) (installed automatically by the setup script if missing)
- Enough disk and RAM for the Kokoro model and PyTorch/torchaudio

## Quick start

1. Clone the repo and enter the project folder:
   ```bash
   cd Kokoro-GUI
   ```

2. Run the setup script (creates a venv, installs dependencies, then starts the server):
   ```bash
   python setup.py
   ```

3. Open **`web_gui.html`** in your browser (double-click or open from your file manager). The page talks to the API at `http://localhost:8000`.

4. Use the UI to choose a voice, enter text, and generate or download audio.

The Flask backend runs at **http://localhost:8000** and loads the Kokoro pipeline once at startup.

## Manual setup (optional)

If you prefer to manage the environment yourself:

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate   # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the API server:
   ```bash
   python api_server.py
   ```

4. Open `web_gui.html` in a browser.

## Project layout

| File / folder   | Purpose |
|-----------------|--------|
| `setup.py`      | One-shot setup: ensures uv, creates `.venv`, installs deps, runs the server |
| `api_server.py` | Flask app: `/voices`, `/synthesize`; uses Kokoro `KPipeline` |
| `web_gui.html`  | Front-end: voice selector, text input, generate/download WAV |
| `requirements.txt` | Python dependencies (Flask, kokoro, torch, torchaudio, etc.) |
| `sample_generate.py` | Minimal CLI example of Kokoro usage (no server) |

## API

- **`GET /voices`** — Returns a JSON list of available Kokoro-82M voice IDs (e.g. `af_heart`, `am_echo`).
- **`POST /synthesize`** — Body: `{ "text": "...", "voice": "af_heart", "speed": 1.0 }`. Returns a WAV file.

## Voices

The server exposes the standard Kokoro-82M voices, including `af_heart`, `af_bella`, `am_adam`, `am_liam`, and others. The default voice is `af_heart`; American English is used (`lang_code='a'`).

## Notes

- First run will download the Kokoro model; later runs use the cached copy.
- The setup script uses **uv** for fast, reliable installs and will install uv via pip if it’s not found.
- Tested on **Python 3.13**; other 3.x versions may work but are unsupported in this repo.
