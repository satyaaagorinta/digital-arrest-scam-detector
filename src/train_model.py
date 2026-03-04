



# import pandas as pd
# from sklearn.model_selection import train_test_split
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.linear_model import LogisticRegression
# from sklearn.metrics import accuracy_score
# import joblib

# # Load dataset
# df = pd.read_csv("data/sms_spam.csv", encoding="latin-1")
# df = df[['v1', 'v2']]
# df.columns = ['label', 'text']
# df['label'] = df['label'].map({'ham': 0, 'spam': 1})

# # Split data
# X_train, X_test, y_train, y_test = train_test_split(
#     df['text'], df['label'], test_size=0.2, random_state=42
# )

# # Convert text to numbers using TF-IDF
# vectorizer = TfidfVectorizer(stop_words='english')
# X_train_vec = vectorizer.fit_transform(X_train)
# X_test_vec = vectorizer.transform(X_test)

# # Train Logistic Regression model
# model = LogisticRegression()
# model.fit(X_train_vec, y_train)

# # Test accuracy
# predictions = model.predict(X_test_vec)
# accuracy = accuracy_score(y_test, predictions)

# print("Model trained successfully!")
# print("Accuracy:", accuracy)

# # Save model
# joblib.dump(model, "models/scam_model.pkl")
# joblib.dump(vectorizer, "models/vectorizer.pkl")

# print("Model saved in models/")


import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

# Load SMS spam dataset
sms_df = pd.read_csv("data/sms_spam.csv", encoding="latin-1")
sms_df = sms_df[['v1', 'v2']]
sms_df.columns = ['label', 'text']
sms_df['label'] = sms_df['label'].map({'ham': 0, 'spam': 1})

# Load digital arrest dataset
digital_df = pd.read_csv("data/digital_arrest_dataset.csv")

# Combine both datasets
df = pd.concat([sms_df, digital_df], ignore_index=True)

# Train test split
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['label'], test_size=0.2, random_state=42
)

# Convert text to numbers
vectorizer = TfidfVectorizer(stop_words='english')
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Train model
model = LogisticRegression()
model.fit(X_train_vec, y_train)

# Evaluate
predictions = model.predict(X_test_vec)
accuracy = accuracy_score(y_test, predictions)

print("Model trained successfully!")
print("Accuracy:", accuracy)

# Save model
joblib.dump(model, "models/scam_model.pkl")
joblib.dump(vectorizer, "models/vectorizer.pkl")

print("Model saved!")