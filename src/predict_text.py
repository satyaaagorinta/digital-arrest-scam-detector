import joblib

# Load saved model
model = joblib.load("models/scam_model.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

print("Scam Detection Ready!")

while True:
    user_input = input("\nEnter message (or type 'exit'): ")

    if user_input.lower() == 'exit':
        break

    # Convert text to vector
    text_vec = vectorizer.transform([user_input])

    # Predict
    prediction = model.predict(text_vec)[0]
    probability = model.predict_proba(text_vec)[0][1]

    if prediction == 1:
        print("⚠️ Scam detected!")
    else:
        print("✅ Looks normal")

    print("Scam Probability:", round(probability, 2))