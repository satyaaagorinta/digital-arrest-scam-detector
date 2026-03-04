import whisper
import joblib
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

# Load models
print("Loading Whisper model...")
whisper_model = whisper.load_model("small")

print("Loading scam detection model...")
model = joblib.load("models/scam_model.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

print("\nReal-time scam detection started...")
print("Listening to microphone...\n")

# Keyword list
danger_keywords = [
    "digital arrest",
    "arrest",
    "police",
    "cyber crime",
    "investigation",
    "money laundering",
    "transfer money",
    "transform money",
    "legal action"
]

sample_rate = 16000
duration = 5  # seconds per chunk


def analyze_audio():
    
    print("Recording...")
    
    # audio = sd.rec(int(duration * sample_rate),
    #                samplerate=sample_rate,
    #                channels=1,
    #                dtype='float32')
    audio = sd.rec(int(duration * sample_rate),
               samplerate=sample_rate,
               channels=1,
               device=2,
               dtype='float32')
    
    sd.wait()

    audio = np.squeeze(audio)

    # Save temporary file
    write("temp.wav", sample_rate, audio)

    # Transcribe
    result = whisper_model.transcribe("temp.wav", fp16=False)
    text = result["text"]

    if len(text.strip()) == 0:
        return

    print("\nTranscription:", text)

    # ML prediction
    text_vec = vectorizer.transform([text])
    probability = model.predict_proba(text_vec)[0][1]

    # Keyword scoring
    keyword_score = 0
    for word in danger_keywords:
        if word in text.lower():
            keyword_score += 0.2

    final_score = probability + keyword_score

    # Decision
    if final_score > 0.6:
        print("⚠️ HIGH FRAUD RISK")
    elif final_score > 0.3:
        print("⚠️ Suspicious conversation")
    else:
        print("✅ Low risk")

    print("ML Probability:", round(probability, 2))
    print("Keyword Score:", round(keyword_score, 2))
    print("Final Score:", round(final_score, 2))
    print("-" * 40)


while True:
    analyze_audio()