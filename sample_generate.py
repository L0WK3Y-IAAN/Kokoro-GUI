from kokoro import KPipeline
import soundfile as sf

# Initialize the pipeline. 'a' is for American English.
# Make sure lang_code matches the voice you choose.
pipeline = KPipeline(lang_code='a')

text = "This is a test of Kokoro running locally on an M4 Max."

# Generate audio using the 'af_heart' voice
generator = pipeline(text, voice='af_heart', speed=1)

for i, (gs, ps, audio) in enumerate(generator):
    # Save the output to a WAV file
    sf.write(f'output_{i}.wav', audio, 24000)
    print(f"Saved output_{i}.wav successfully!")
    