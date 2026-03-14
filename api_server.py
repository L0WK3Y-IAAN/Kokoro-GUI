import io
import sys
import numpy as np
import soundfile as sf
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Lazy Load Kokoro Pipelines (Saves RAM)
# ---------------------------------------------------------------------------
pipelines = {}

def get_pipeline(lang_code):
    """Loads a language model into memory only when it is actually requested."""
    if lang_code not in pipelines:
        print(f"[*] Loading Kokoro pipeline for language '{lang_code}'...")
        from kokoro import KPipeline
        pipelines[lang_code] = KPipeline(lang_code=lang_code)
    return pipelines[lang_code]

# Preload American English to ensure fast first-startup for the default voice
try:
    print("Loading Base Kokoro TTS pipeline into memory...")
    get_pipeline('a')
    print("[+] Base model loaded successfully!")
except Exception as e:
    print(f"[!] Failed to load base model: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Global Voices Database (Kokoro v1.0)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Global Voices Database (Kokoro v1.0)
# ---------------------------------------------------------------------------
VOICE_REGIONS = {
    "🇺🇸 American English": [
        "af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", "af_kore", 
        "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky", "am_adam", 
        "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", 
        "am_puck", "am_santa"
    ],
    "🇬🇧 British English": [
        "bf_alice", "bf_emma", "bf_isabella", "bf_lily", 
        "bm_daniel", "bm_fable", "bm_george", "bm_lewis"
    ],
    "🇫🇷 French": [
        "ff_siwis"
    ],
    "🇮🇹 Italian": [
        "if_sara", "im_nicola"
    ],
    "🇯🇵 Japanese": [
        "jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo"
    ],
    "🇪🇸 Spanish": [
        "ef_dora", "em_alex", "em_santa"
    ],
    "🇨🇳 Mandarin Chinese": [
        "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi", "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"
    ],
    "🇮🇳 Hindi": [
        "hf_alpha", "hf_beta", "hm_omega", "hm_psi"
    ],
    "🇧🇷 Brazilian Portuguese": [
        "pf_dora", "pm_alex", "pm_santa"
    ]
}


# Flatten the dictionary into a single set for fast validation
ALL_VOICES = {voice for voices in VOICE_REGIONS.values() for voice in voices}
SAMPLE_RATE = 24_000 

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/voices", methods=["GET"])
def get_voices():
    """Return the structured dictionary of regions and their voices."""
    return jsonify({"regions": VOICE_REGIONS})

@app.route("/synthesize", methods=["POST"])
def synthesize():
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in JSON body"}), 400

    text = data["text"]
    voice = data.get("voice", "af_heart")
    speed = float(data.get("speed", 1.0))

    if voice not in ALL_VOICES:
        return jsonify({"error": f"Unknown voice '{voice}'."}), 400

    try:
        # The first character of the voice name defines the language code 
        # (e.g. 'a' for American, 'b' for British, 'j' for Japanese)
        lang_code = voice[0]
        active_pipeline = get_pipeline(lang_code)

        generator = active_pipeline(
            text,
            voice=voice,
            speed=speed,
            split_pattern=r'\n+'
        )

        chunks = [audio for _, _, audio in generator]

        if not chunks:
            return jsonify({"error": "No audio generated from the provided text"}), 500

        final_audio = np.concatenate(chunks)

        wav_buf = io.BytesIO()
        sf.write(wav_buf, final_audio, SAMPLE_RATE, format="WAV")
        wav_buf.seek(0)

        return send_file(
            wav_buf,
            mimetype="audio/wav",
            as_attachment=True,
            download_name="output.wav"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
