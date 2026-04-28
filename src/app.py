# import streamlit as st
# import whisper
# import joblib
# import sounddevice as sd
# import numpy as np
# from scipy.io.wavfile import write
# import plotly.graph_objects as go

# # ---------------------------
# # Load Models (cached)
# # ---------------------------
# @st.cache_resource
# def load_models():
#     whisper_model = whisper.load_model("small")
#     model = joblib.load("models/scam_model.pkl")
#     vectorizer = joblib.load("models/vectorizer.pkl")
#     return whisper_model, model, vectorizer

# whisper_model, model, vectorizer = load_models()

# # ---------------------------
# # Keywords
# # ---------------------------
# danger_keywords = [
#     "digital arrest", "arrest", "police", "cyber crime",
#     "investigation", "money laundering", "transfer money",
#     "transform money", "legal action", "warrant",
#     "compliance", "verification", "fraud investigation",
#     "case number", "law enforcement", "financial crime",
#     "identity verification", "illegal activity",
#     "frozen account", "legal consequences"
# ]

# # ---------------------------
# # UI Title
# # ---------------------------
# st.title("🔐 Real-Time Scam Detection System")

# st.write("Press the button and speak into your microphone.")

# # ---------------------------
# # Recording duration
# # ---------------------------
# duration = st.slider("Recording Duration (seconds)", 3, 10, 5)

# # ---------------------------
# # Record Button
# # ---------------------------
# if st.button("🎤 Start Recording"):

#     st.info("Recording... Speak now")

#     sample_rate = 16000

#     audio = sd.rec(int(duration * sample_rate),
#                    samplerate=sample_rate,
#                    channels=1,
#                    dtype='float32')

#     sd.wait()

#     audio = np.squeeze(audio)

#     write("temp.wav", sample_rate, audio)

#     st.success("Recording complete")

#     # ---------------------------
#     # Transcription
#     # ---------------------------
#     st.info("Transcribing...")

#     result = whisper_model.transcribe("temp.wav", fp16=False)
#     text = result["text"]

#     st.subheader("📝 Transcription")
#     st.write(text)

#     # ---------------------------
#     # ML Prediction
#     # ---------------------------
#     text_vec = vectorizer.transform([text])
#     probability = model.predict_proba(text_vec)[0][1]

#     # ---------------------------
#     # Keyword Detection
#     # ---------------------------
#     keyword_score = 0
#     for word in danger_keywords:
#         if word in text.lower():
#             keyword_score += 0.2

#     final_score = probability + keyword_score

#     # Clamp score between 0 and 1
#     final_score = min(final_score, 1.0)

   
#     st.subheader("📊 Risk Meter")

#     fig = go.Figure(go.Indicator(
#         mode="gauge+number",
#         value=final_score * 100,
#         title={'text': "Fraud Risk (%)"},
#         gauge={
#             'axis': {'range': [0, 100]},
#             'bar': {'thickness': 0.3},
#             'steps': [
#                 {'range': [0, 30], 'color': "green"},
#                 {'range': [30, 60], 'color': "yellow"},
#                 {'range': [60, 100], 'color': "red"}
#             ],
#         }
#     ))

#     st.plotly_chart(fig)

    
#     st.subheader("🚨 Detection Result")

#     if final_score > 0.6:
#         st.error("⚠️ HIGH FRAUD RISK")
#     elif final_score > 0.3:
#         st.warning("⚠️ Suspicious Conversation")
#     else:
#         st.success("✅ Low Risk")

   
#     st.write("ML Probability:", round(probability, 2))
#     st.write("Keyword Score:", round(keyword_score, 2))
#     st.write("Final Risk Score:", round(final_score, 2))







import streamlit as st
import whisper
import joblib
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import plotly.graph_objects as go
import time

# ---------------------------
# Load models
# ---------------------------
@st.cache_resource
def load_models():
    whisper_model = whisper.load_model("small")
    model = joblib.load("models/scam_model.pkl")
    vectorizer = joblib.load("models/vectorizer.pkl")
    return whisper_model, model, vectorizer

whisper_model, model, vectorizer = load_models()

# ---------------------------
# Keywords
# ---------------------------
danger_keywords = [
    "digital arrest", "arrest", "police", "cyber crime",
    "investigation", "money laundering", "transfer money",
    "legal action", "warrant", "verification",
    "fraud investigation", "law enforcement",
    "illegal activity", "frozen account"
]

# ---------------------------
# UI
# ---------------------------
st.title("🔴 Live Scam Detection Monitor")

if "running" not in st.session_state:
    st.session_state.running = False

# Buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Start Monitoring"):
        st.session_state.running = True

with col2:
    if st.button("⏹ Stop"):
        st.session_state.running = False

# Placeholder for dynamic UI
placeholder = st.empty()

# ---------------------------
# Main Loop
# ---------------------------
if st.session_state.running:

    while st.session_state.running:

        with placeholder.container():

            st.info("🎤 Listening... (15 sec chunk)")

            # ---------------------------
            # Record audio
            # ---------------------------
            duration = 15
            sample_rate = 16000

            audio = sd.rec(int(duration * sample_rate),
                           samplerate=sample_rate,
                           channels=1,
                           dtype='float32')

            sd.wait()

            audio = np.squeeze(audio)
            write("temp.wav", sample_rate, audio)

            # ---------------------------
            # Transcription
            # ---------------------------
            result = whisper_model.transcribe("temp.wav", fp16=False)
            text = result["text"]

            st.subheader("📝 Latest Transcription")
            st.write(text)

            # ---------------------------
            # ML Prediction
            # ---------------------------
            text_vec = vectorizer.transform([text])
            probability = model.predict_proba(text_vec)[0][1]

            # ---------------------------
            # Keyword Detection
            # ---------------------------
            keyword_score = 0
            for word in danger_keywords:
                if word in text.lower():
                    keyword_score += 0.2

            final_score = min(probability + keyword_score, 1.0)

            # ---------------------------
            # Risk Meter
            # ---------------------------
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=final_score * 100,
                title={'text': "Fraud Risk (%)"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'steps': [
                        {'range': [0, 30], 'color': "green"},
                        {'range': [30, 60], 'color': "yellow"},
                        {'range': [60, 100], 'color': "red"}
                    ],
                }
            ))

            st.plotly_chart(fig, use_container_width=True)

            # ---------------------------
            # Result
            # ---------------------------
            if final_score > 0.6:
                st.error("⚠️ HIGH FRAUD RISK")
            elif final_score > 0.3:
                st.warning("⚠️ Suspicious")
            else:
                st.success("✅ Safe")

            st.write("ML:", round(probability, 2),
                     "| Keywords:", round(keyword_score, 2),
                     "| Final:", round(final_score, 2))

        # small delay before next cycle
        time.sleep(1)


# import streamlit as st
# from faster_whisper import WhisperModel
# import joblib
# import sounddevice as sd
# import numpy as np
# from scipy.io.wavfile import write
# import time

# # ---------------------------
# # CONFIG
# # ---------------------------
# st.set_page_config(page_title="Scam Detector", layout="centered")

# # ---------------------------
# # LOAD MODELS
# # ---------------------------
# @st.cache_resource
# def load_models():
#     whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
#     model = joblib.load("models/scam_model.pkl")
#     vectorizer = joblib.load("models/vectorizer.pkl")
#     return whisper_model, model, vectorizer

# whisper_model, model, vectorizer = load_models()

# # ---------------------------
# # KEYWORDS
# # ---------------------------
# danger_keywords = [
#     "digital arrest","arrest","police","cyber crime",
#     "investigation","money laundering","transfer money",
#     "legal action","warrant","verification",
#     "fraud investigation","law enforcement"
# ]

# # ---------------------------
# # STATE
# # ---------------------------
# if "running" not in st.session_state:
#     st.session_state.running = False

# if "score" not in st.session_state:
#     st.session_state.score = 0

# # ---------------------------
# # HEADER
# # ---------------------------
# st.markdown(
#     "<h1 style='text-align:center;'>🎤 Voice Scam Monitor</h1>",
#     unsafe_allow_html=True
# )

# st.markdown("---")

# # ---------------------------
# # CONTROL PANEL
# # ---------------------------
# col1, col2 = st.columns(2)

# with col1:
#     if st.button("▶ Start", use_container_width=True):
#         st.session_state.running = True

# with col2:
#     if st.button("⏹ Stop", use_container_width=True):
#         st.session_state.running = False

# st.markdown("---")

# # ---------------------------
# # MAIN DISPLAY CARD
# # ---------------------------
# card = st.container()

# with card:

#     transcription_placeholder = st.empty()
#     progress_placeholder = st.empty()
#     result_placeholder = st.empty()

# # ---------------------------
# # RUN LOGIC (NO LOOP)
# # ---------------------------
# if st.session_state.running:

#     # RECORD
#     duration = 6
#     sample_rate = 16000

#     transcription_placeholder.info("🎧 Listening...")

#     audio = sd.rec(int(duration * sample_rate),
#                    samplerate=sample_rate,
#                    channels=1,
#                    dtype='float32')
#     sd.wait()

#     audio = np.squeeze(audio)
#     write("temp.wav", sample_rate, audio)

#     # TRANSCRIBE
#     segments, _ = whisper_model.transcribe("temp.wav")
#     text = " ".join([seg.text for seg in segments])

#     transcription_placeholder.markdown(f"**📝 {text}**")

#     # ML
#     text_vec = vectorizer.transform([text])
#     probability = model.predict_proba(text_vec)[0][1]

#     # KEYWORDS
#     text_lower = text.lower()
#     keyword_score = sum(0.35 for w in danger_keywords if w in text_lower)

#     final_score = min(probability + keyword_score, 1.0)

#     # SMOOTH
#     # final_score = 0.7 * st.session_state.score + 0.3 * final_score
#     final_score =  final_score
#     st.session_state.score = final_score

#     # PROGRESS BAR
#     progress_placeholder.progress(final_score)

#     # RESULT (ONLY ONE BOX)
#     if final_score > 0.6:
#         result_placeholder.error("⚠ HIGH FRAUD RISK")
#     elif final_score > 0.3:
#         result_placeholder.warning("⚠ Suspicious")
#     else:
#         result_placeholder.success("✅ Safe")

#     # AUTO REFRESH (SMOOTH)
#     time.sleep(0.5)
#     st.rerun()

