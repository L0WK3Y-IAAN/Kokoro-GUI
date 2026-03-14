from flask import Flask, request, send_file, jsonify
from flask_cors import CORS 
from kokoro import KPipeline
import soundfile as sf
import numpy as np
import io
import sys

app = Flask(__name__)
CORS(app)

# Initialize the pipeline globally so it only loads once at startup
print("🎯 Loading Kokoro TTS pipeline into memory...")
try:
    # Use lang_code='a' for American English, 'b' for British English
    pipeline = KPipeline(lang_code='a')
    print("✓ Model loaded successfully!")
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    sys.exit(1)

# List of standard Kokoro-82M voices
AVAILABLE_VOICES = [
    "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica", 
    "af_kore", "af_nicole", "af_nova", "af_river", "af_sky", 
    "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", 
    "am_michael", "am_onyx", "am_puck"
]

@app.route('/voices', methods=['GET'])
def get_voices():
    """Return a list of available standard voices."""
    return jsonify({"voices": AVAILABLE_VOICES})

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Generate audio from text and return it as a WAV file."""
    data = request.json
    
    # Validate request
    if not data or 'text' not in data:
        return jsonify({"error": "Missing 'text' in JSON body"}), 400
        
    text = data.get('text')
    voice = data.get('voice', 'af_heart')  # Default voice if none provided
    speed = float(data.get('speed', 1.0))
    
    try:
        # Generate audio chunks
        generator = pipeline(
            text, 
            voice=voice, 
            speed=speed, 
            split_pattern=r'\n+'
        )
        
        audio_chunks = []
        sample_rate = 24000 # Kokoro outputs 24kHz audio
        
        # Process generator output and collect audio
        for _, _, audio in generator:
            audio_chunks.append(audio)
            
        if not audio_chunks:
            return jsonify({"error": "No audio generated from the provided text"}), 500
            
        # Combine all audio chunks into a single NumPy array
        final_audio = np.concatenate(audio_chunks)
        
        # Write the numpy array to an in-memory BytesIO buffer as a WAV file
        wav_io = io.BytesIO()
        sf.write(wav_io, final_audio, sample_rate, format='WAV')
        
        # Reset buffer position to the beginning before sending
        wav_io.seek(0)
        
        # Return as WAV file directly from memory
        return send_file(
            wav_io,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='output.wav'
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=8000, debug=True)
