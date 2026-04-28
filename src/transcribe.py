import whisper

print("Loading Whisper model...")
model = whisper.load_model("small")  
# from faster_whisper import WhisperModel

# model = WhisperModel(
#     "base", 
#     device="cpu", 
#     compute_type="int8"   
# )

print("Model loaded!")

result = model.transcribe("sample.wav")

print("\nTranscription:")
# segments, _ = model.transcribe("temp.wav")

# text = " ".join([seg.text for seg in segments])
print(result["text"])