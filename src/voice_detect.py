# import whisper
# import joblib

# print("Loading Whisper model...")
# whisper_model = whisper.load_model("small")

# print("Loading scam detection model...")
# model = joblib.load("models/scam_model.pkl")
# vectorizer = joblib.load("models/vectorizer.pkl")

# print("\nSystem Ready!")

# # Transcribe audio
# result = whisper_model.transcribe("sample.wav", fp16=False)

# text = result["text"]

# print("\nTranscription:")
# print(text)

# # Convert text to vector
# text_vec = vectorizer.transform([text])

# # Predict scam probability
# prediction = model.predict(text_vec)[0]
# probability = model.predict_proba(text_vec)[0][1]

# print("\nDetection Result:")

# if prediction == 1:
#     print("⚠️ Scam detected!")
# else:
#     print("✅ Looks normal")

# print("Scam probability:", round(probability, 2))

# danger_keywords = [
#     "digital arrest",
#     "arrest",
#     "police",
#     "cyber crime",
#     "investigation",
#     "money laundering",
#     "transfer money",
#     "legal action"
# ]

# keyword_score = 0

# for word in danger_keywords:
#     if word in text.lower():
#         keyword_score += 0.2

# final_score = probability + keyword_score


import whisper
import joblib

# Load Whisper model
print("Loading Whisper model...")
whisper_model = whisper.load_model("small")   # use "small" for better accuracy

# Load scam detection model
print("Loading scam detection model...")
model = joblib.load("models/scam_model.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

print("\nSystem Ready!")

# Transcribe audio file
result = whisper_model.transcribe("sample.wav", fp16=False)
text = result["text"]

print("\nTranscription:")
print(text)

# Convert text into vector for ML model
text_vec = vectorizer.transform([text])

# ML prediction
prediction = model.predict(text_vec)[0]
probability = model.predict_proba(text_vec)[0][1]

# -------------------------------
# Keyword detection layer
# -------------------------------

danger_keywords = [
    "digital arrest",
    "arrest",
    "police",
    "cyber crime",
    "investigation",
    "money laundering",
    "transfer money",
    "transform money", 
    "warrant",
    "compliance",
    "verification",
    "fraud investigation",
    "case number",
    "law enforcement",
    "financial crime",
    "identity verification",
    "illegal activity",
    "frozen account",
    "legal consequences",
    "investigation officer",
    "fraud complaint",
    "cyber enforcement",  
    "legal action",
    "financial scrutiny"
]

keyword_score = 0

for word in danger_keywords:
    if word in text.lower():
        keyword_score += 0.2

# Combine ML probability + keyword score
final_score = probability + keyword_score

# -------------------------------
# Final Decision
# -------------------------------

print("\nDetection Result:")

if final_score > 0.6:
    print("⚠️ High fraud risk detected")
elif final_score > 0.3:
    print("⚠️ Suspicious call")
else:
    print("✅ Low risk")

print("\nML Probability:", round(probability, 2))
print("Keyword Score:", round(keyword_score, 2))
print("Final Risk Score:", round(final_score, 2))