import whisper

print("Loading Whisper model...")
model = whisper.load_model("small")  # use tiny first (faster)

print("Model loaded!")

result = model.transcribe("sample.wav")

print("\nTranscription:")
print(result["text"])