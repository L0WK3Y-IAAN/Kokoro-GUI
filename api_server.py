import io
import sys
import numpy as np
import soundfile as sf
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Load the Kokoro pipeline once at startup
# ---------------------------------------------------------------------------
print("Loading Kokoro TTS pipeline into memory...")
try:
    from kokoro import KPipeline
    # lang_code='a' = American English, 'b' = British English
    pipeline = KPipeline(lang_code='a')
    print("[+] Model loaded successfully!")
except ImportError as e:
    print(f"[!] Could not import kokoro: {e}")
    print("    Make sure you ran setup.py and are using the .venv Python.")
    sys.exit(1)
except Exception as e:
    print(f"[!] Failed to load model: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Available voices
# ---------------------------------------------------------------------------
AVAILABLE_VOICES = [
    "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica",
    "af_kore",  "af_nicole", "af_nova",  "af_river", "af_sky",
    "am_adam",  "am_echo",   "am_eric",  "am_fenrir", "am_liam",
    "am_michael", "am_onyx", "am_puck",
]

SAMPLE_RATE = 24_000  # Kokoro outputs 24 kHz

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/voices", methods=["GET"])
def get_voices():
    """Return the list of available voices."""
    return jsonify({"voices": AVAILABLE_VOICES})


@app.route("/synthesize", methods=["POST"])
def synthesize():
    """Synthesise text and return a WAV file."""
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in JSON body"}), 400

    text  = data["text"]
    voice = data.get("voice", "af_heart")
    speed = float(data.get("speed", 1.0))

    if voice not in AVAILABLE_VOICES:
        return jsonify({
            "error": f"Unknown voice '{voice}'.",
            "available_voices": AVAILABLE_VOICES,
        }), 400

    try:
        generator = pipeline(
            text,
            voice=voice,
            speed=speed,
            split_pattern=r'\n+',
        )

        chunks = [audio for _, _, audio in generator]

        if not chunks:
            return jsonify({"error": "No audio generated from the provided text"}), 500

        final_audio = np.concatenate(chunks)

        # Write to an in-memory WAV buffer — works identically on all OSes
        wav_buf = io.BytesIO()
        sf.write(wav_buf, final_audio, SAMPLE_RATE, format="WAV")
        wav_buf.seek(0)

        return send_file(
            wav_buf,
            mimetype="audio/wav",
            as_attachment=True,
            download_name="output.wav",   # Flask ≥2.0; ignored gracefully on older
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # host='0.0.0.0' makes the server reachable on the local network.
    # Set debug=False in production.
    app.run(host="0.0.0.0", port=8000, debug=False)
