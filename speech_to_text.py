import whisper

# Load once globally (VERY IMPORTANT)
model = whisper.load_model("base", device="cpu")
def transcribe_audio(audio_path):
    try:
        result = model.transcribe(
            audio_path,
            fp16=False  # safer for CPU
        )

        text = result["text"].strip()

        print("📝 Transcribed Text:", text)

        return text

    except Exception as e:
        print("Whisper Error:", e)
        return None
