







# import streamlit as st
# import whisper
# import joblib
# import sounddevice as sd
# import numpy as np
# from scipy.io.wavfile import write
# import plotly.graph_objects as go
# import time

# # ---------------------------
# # Load models
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
#     "legal action", "warrant", "verification",
#     "fraud investigation", "law enforcement",
#     "illegal activity", "frozen account"
# ]

# # ---------------------------
# # UI
# # ---------------------------
# st.title("🔴 Live Scam Detection Monitor")

# if "running" not in st.session_state:
#     st.session_state.running = False

# # Buttons
# col1, col2 = st.columns(2)

# with col1:
#     if st.button("▶ Start Monitoring"):
#         st.session_state.running = True

# with col2:
#     if st.button("⏹ Stop"):
#         st.session_state.running = False

# # Placeholder for dynamic UI
# placeholder = st.empty()

# # ---------------------------
# # Main Loop
# # ---------------------------
# if st.session_state.running:

#     while st.session_state.running:

#         with placeholder.container():

#             st.info("🎤 Listening... (15 sec chunk)")

#             # ---------------------------
#             # Record audio
#             # ---------------------------
#             duration = 15
#             sample_rate = 16000

#             audio = sd.rec(int(duration * sample_rate),
#                            samplerate=sample_rate,
#                            channels=1,
#                            dtype='float32')

#             sd.wait()

#             audio = np.squeeze(audio)
#             write("temp.wav", sample_rate, audio)

#             # ---------------------------
#             # Transcription
#             # ---------------------------
#             result = whisper_model.transcribe("temp.wav", fp16=False)
#             text = result["text"]

#             st.subheader("📝 Latest Transcription")
#             st.write(text)

#             # ---------------------------
#             # ML Prediction
#             # ---------------------------
#             text_vec = vectorizer.transform([text])
#             probability = model.predict_proba(text_vec)[0][1]

#             # ---------------------------
#             # Keyword Detection
#             # ---------------------------
#             keyword_score = 0
#             for word in danger_keywords:
#                 if word in text.lower():
#                     keyword_score += 0.2

#             final_score = min(probability + keyword_score, 1.0)

#             # ---------------------------
#             # Risk Meter
#             # ---------------------------
#             fig = go.Figure(go.Indicator(
#                 mode="gauge+number",
#                 value=final_score * 100,
#                 title={'text': "Fraud Risk (%)"},
#                 gauge={
#                     'axis': {'range': [0, 100]},
#                     'steps': [
#                         {'range': [0, 30], 'color': "green"},
#                         {'range': [30, 60], 'color': "yellow"},
#                         {'range': [60, 100], 'color': "red"}
#                     ],
#                 }
#             ))

#             st.plotly_chart(fig, use_container_width=True)

#             # ---------------------------
#             # Result
#             # ---------------------------
#             if final_score > 0.6:
#                 st.error("⚠️ HIGH FRAUD RISK")
#             elif final_score > 0.3:
#                 st.warning("⚠️ Suspicious")
#             else:
#                 st.success("✅ Safe")

#             st.write("ML:", round(probability, 2),
#                      "| Keywords:", round(keyword_score, 2),
#                      "| Final:", round(final_score, 2))

#         # small delay before next cycle
#         time.sleep(1)


import streamlit as st
import whisper
import joblib
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import plotly.graph_objects as go
import time
import datetime

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="Digital Arrest Scam Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------
# Custom CSS - Dark Red/Orange Theme
# ---------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        background-color: #0a0a0a !important;
        color: #e0e0e0;
        font-family: 'Rajdhani', sans-serif;
    }
    .stApp {
        background: #0a0a0a;
        background-image:
            radial-gradient(ellipse at 15% 15%, #1a050088 0%, transparent 45%),
            radial-gradient(ellipse at 85% 85%, #0d0d0088 0%, transparent 45%);
    }

    /* Hide streamlit default chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main header */
    .main-header {
        text-align: center;
        padding: 28px 0 16px 0;
        border-bottom: 1px solid #ff220044;
        margin-bottom: 28px;
    }
    .main-header h1 {
        font-family: 'Share Tech Mono', monospace;
        font-size: 2.4rem;
        color: #ff2200;
        letter-spacing: 6px;
        text-shadow: 0 0 30px #ff220055, 0 0 60px #ff220022;
        margin: 0;
    }
    .main-header .subtitle {
        color: #ff6600;
        font-size: 0.8rem;
        letter-spacing: 4px;
        margin: 8px 0 0 0;
        text-transform: uppercase;
        opacity: 0.8;
    }

    /* Cards */
    .card {
        background: #111111;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 16px;
    }
    .card-red { border-left: 3px solid #ff2200; }
    .card-orange { border-left: 3px solid #ff6600; }
    .card-green { border-left: 3px solid #00cc44; }

    /* Section titles */
    .section-title {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.72rem;
        color: #555;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    /* Listening indicator */
    .listening-indicator {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.9rem;
        color: #ff2200;
        letter-spacing: 2px;
    }
    .dot {
        width: 10px; height: 10px;
        background: #ff2200;
        border-radius: 50%;
        box-shadow: 0 0 10px #ff2200;
        animation: blink 0.8s infinite;
        display: inline-block;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.15; }
    }

    /* Status badges */
    .status-safe {
        background: #001a0a; border: 1px solid #00cc44;
        color: #00cc44; padding: 12px 20px; border-radius: 6px;
        font-family: 'Share Tech Mono', monospace; font-size: 1.3rem;
        text-align: center; letter-spacing: 3px;
        text-shadow: 0 0 12px #00cc4466;
    }
    .status-warning {
        background: #1a0d00; border: 1px solid #ff6600;
        color: #ff6600; padding: 12px 20px; border-radius: 6px;
        font-family: 'Share Tech Mono', monospace; font-size: 1.3rem;
        text-align: center; letter-spacing: 3px;
        text-shadow: 0 0 12px #ff660066;
    }
    .status-danger {
        background: #1a0000; border: 1px solid #ff2200;
        color: #ff2200; padding: 12px 20px; border-radius: 6px;
        font-family: 'Share Tech Mono', monospace; font-size: 1.3rem;
        text-align: center; letter-spacing: 3px;
        text-shadow: 0 0 12px #ff220066;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 10px #ff220033; }
        50% { opacity: 0.7; box-shadow: 0 0 25px #ff220066; }
    }

    /* Metric boxes */
    .metrics-row {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
    }
    .metric-box {
        flex: 1;
        background: #111;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 14px 10px;
        text-align: center;
    }
    .metric-label {
        font-size: 0.68rem;
        color: #444;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-value {
        font-family: 'Share Tech Mono', monospace;
        font-size: 1.7rem;
        color: #ff6600;
    }
    .metric-value.green { color: #00cc44; }
    .metric-value.red { color: #ff2200; }

    /* Transcript box */
    .transcript-box {
        background: #0d0d0d;
        border: 1px solid #1e1e1e;
        border-radius: 6px;
        padding: 14px 16px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.88rem;
        color: #999;
        min-height: 70px;
        line-height: 1.7;
        word-break: break-word;
    }

    /* History log */
    .history-entry {
        background: #0d0d0d;
        border: 1px solid #1a1a1a;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .history-time {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.7rem;
        color: #444;
        margin-bottom: 5px;
    }
    .history-text {
        color: #aaa;
        font-size: 0.88rem;
        margin-bottom: 6px;
        line-height: 1.5;
    }
    .history-score {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.78rem;
    }
    .safe-tag { color: #00cc44; }
    .warn-tag { color: #ff6600; }
    .danger-tag { color: #ff2200; }

    /* Buttons */
    div[data-testid="column"] .stButton > button {
        width: 100%;
        font-family: 'Share Tech Mono', monospace;
        letter-spacing: 2px;
        font-size: 0.95rem;
        height: 48px;
        border-radius: 6px;
        border: none;
        transition: all 0.2s ease;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 3px; }
    ::-webkit-scrollbar-track { background: #111; }
    ::-webkit-scrollbar-thumb { background: #ff2200; border-radius: 2px; }

    /* Plotly chart background fix */
    .js-plotly-plot { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Load Models
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
    "illegal activity", "frozen account", "case number",
    "compliance", "financial crime", "identity verification",
    "legal consequences", "investigation officer",
    "fraud complaint", "cyber enforcement", "financial scrutiny"
]

# ---------------------------
# Session State Init
# ---------------------------
if "running" not in st.session_state:
    st.session_state.running = False
if "history" not in st.session_state:
    st.session_state.history = []
if "current_score" not in st.session_state:
    st.session_state.current_score = 0.0
if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0
if "high_risk_count" not in st.session_state:
    st.session_state.high_risk_count = 0
if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = "—"

# ---------------------------
# Header
# ---------------------------
st.markdown("""
<div class="main-header">
    <h1>🛡️ SCAM SHIELD</h1>
    <div class="subtitle">Real-Time Digital Arrest Scam Detection System</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Layout: Left (controls + status) | Right (history)
# ---------------------------
left_col, right_col = st.columns([3, 2], gap="large")

with left_col:

    # --- Control Buttons ---
    c1, c2 = st.columns(2)
    with c1:
        start_btn = st.button("▶  START MONITORING", type="primary", use_container_width=True)
    with c2:
        stop_btn = st.button("⏹  STOP", type="secondary", use_container_width=True)

    if start_btn:
        st.session_state.running = True
    if stop_btn:
        st.session_state.running = False

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # --- Metrics Row ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Chunks Analyzed</div>
            <div class="metric-value">{st.session_state.total_chunks}</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        risk_color = "red" if st.session_state.high_risk_count > 0 else "green"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">High Risk Events</div>
            <div class="metric-value {risk_color}">{st.session_state.high_risk_count}</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        score_pct = int(st.session_state.current_score * 100)
        score_color = "red" if score_pct > 60 else ("green" if score_pct < 30 else "")
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Current Risk</div>
            <div class="metric-value {score_color}">{score_pct}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # --- Risk Gauge ---
    gauge_placeholder = st.empty()
    status_placeholder = st.empty()
    waveform_placeholder = st.empty()
    transcript_placeholder = st.empty()
    score_detail_placeholder = st.empty()

    def render_gauge(score):
        val = score * 100
        if val > 60:
            bar_color = "#ff2200"
            needle_color = "#ff0000"
        elif val > 30:
            bar_color = "#ff6600"
            needle_color = "#ff6600"
        else:
            bar_color = "#00cc44"
            needle_color = "#00cc44"

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            number={
                'suffix': "%",
                'font': {'color': bar_color, 'size': 36, 'family': 'Share Tech Mono'}
            },
            title={
                'text': "FRAUD RISK",
                'font': {'color': '#555', 'size': 13, 'family': 'Share Tech Mono'}
            },
            gauge={
                'axis': {
                    'range': [0, 100],
                    'tickcolor': '#333',
                    'tickfont': {'color': '#555', 'size': 10},
                    'tickwidth': 1,
                },
                'bar': {'color': bar_color, 'thickness': 0.25},
                'bgcolor': '#111',
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 30], 'color': '#001a0a'},
                    {'range': [30, 60], 'color': '#1a0d00'},
                    {'range': [60, 100], 'color': '#1a0000'},
                ],
                'threshold': {
                    'line': {'color': needle_color, 'width': 3},
                    'thickness': 0.85,
                    'value': val
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': '#e0e0e0'},
            height=260,
            margin=dict(t=40, b=10, l=20, r=20)
        )
        return fig

    def render_waveform(audio_data):
        """Render audio waveform using plotly"""
        # Downsample for display
        step = max(1, len(audio_data) // 500)
        wave = audio_data[::step]
        x = np.linspace(0, len(audio_data) / 16000, len(wave))

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=wave,
            mode='lines',
            line=dict(color='#ff4400', width=1),
            fill='tozeroy',
            fillcolor='rgba(255,68,0,0.08)'
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=100,
            margin=dict(t=5, b=5, l=5, r=5),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, color='#333'),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-1, 1]),
            showlegend=False
        )
        return fig

    # Initial gauge
    gauge_placeholder.plotly_chart(render_gauge(0), use_container_width=True)

    # Initial status
    status_placeholder.markdown(
        '<div class="status-safe">⬤ &nbsp; SYSTEM READY</div>',
        unsafe_allow_html=True
    )

    # Initial transcript
    transcript_placeholder.markdown("""
    <div class='card card-orange'>
        <div class='section-title'>Latest Transcription</div>
        <div class='transcript-box'>Waiting for audio input...</div>
    </div>
    """, unsafe_allow_html=True)

with right_col:
    st.markdown("""
    <div class='section-title' style='margin-bottom:12px;'>
        📋 &nbsp; CONVERSATION HISTORY LOG
    </div>
    """, unsafe_allow_html=True)

    history_placeholder = st.empty()

    def render_history():
        if not st.session_state.history:
            history_placeholder.markdown("""
            <div style='color:#333; font-family: Share Tech Mono, monospace;
                        font-size:0.8rem; letter-spacing:2px; text-align:center;
                        padding:40px 0;'>
                NO ENTRIES YET
            </div>
            """, unsafe_allow_html=True)
        else:
            html = ""
            for entry in reversed(st.session_state.history[-20:]):
                score_pct = int(entry['score'] * 100)
                if entry['score'] > 0.6:
                    tag_class = "danger-tag"
                    badge = f"⚠ HIGH RISK — {score_pct}%"
                elif entry['score'] > 0.3:
                    tag_class = "warn-tag"
                    badge = f"⚡ SUSPICIOUS — {score_pct}%"
                else:
                    tag_class = "safe-tag"
                    badge = f"✓ SAFE — {score_pct}%"

                keywords_found = [kw for kw in danger_keywords if kw in entry['text'].lower()]
                kw_html = ""
                if keywords_found:
                    kw_html = f"<div style='font-size:0.72rem; color:#ff4400; margin-top:4px;'>🔑 {', '.join(keywords_found[:4])}</div>"

                html += f"""
                <div class="history-entry">
                    <div class="history-time">{entry['time']}</div>
                    <div class="history-text">{entry['text'][:180]}{'...' if len(entry['text']) > 180 else ''}</div>
                    {kw_html}
                    <div class="history-score {tag_class}">{badge}</div>
                </div>
                """
            history_placeholder.markdown(html, unsafe_allow_html=True)

    render_history()

# ---------------------------
# Main Detection Loop
# ---------------------------
if st.session_state.running:

    duration = 10
    sample_rate = 16000

    while st.session_state.running:

        # Listening indicator
        with left_col:
            status_placeholder.markdown(
                '<div class="status-warning"><span class="dot"></span> &nbsp; LISTENING...</div>',
                unsafe_allow_html=True
            )

        # Record audio
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        audio = np.squeeze(audio)
        write("temp.wav", sample_rate, audio)

        # Show waveform
        with left_col:
            waveform_placeholder.plotly_chart(
                render_waveform(audio),
                use_container_width=True
            )

        # Transcribe
        result = whisper_model.transcribe("temp.wav", fp16=False)
        text = result["text"].strip()

        if not text:
            with left_col:
                status_placeholder.markdown(
                    '<div class="status-safe">🔇 &nbsp; NO SPEECH DETECTED</div>',
                    unsafe_allow_html=True
                )
            time.sleep(1)
            continue

        # ML Prediction
        text_vec = vectorizer.transform([text])
        probability = model.predict_proba(text_vec)[0][1]

        # Keyword Scoring
        keyword_score = 0
        for word in danger_keywords:
            if word in text.lower():
                keyword_score += 0.2

        # Final Score with smooth update
        raw_score = min(probability + keyword_score, 1.0)
        prev = st.session_state.current_score
        if raw_score > prev:
            new_score = prev + (raw_score - prev) * 0.8   # fast increase
        else:
            new_score = prev + (raw_score - prev) * 0.3   # slow decrease
        st.session_state.current_score = new_score

        # Update counters
        st.session_state.total_chunks += 1
        if new_score > 0.6:
            st.session_state.high_risk_count += 1

        # Save to history
        st.session_state.history.append({
            'time': datetime.datetime.now().strftime("%H:%M:%S"),
            'text': text,
            'score': new_score,
            'ml': probability,
            'keywords': keyword_score
        })

        # Update UI
        with left_col:
            # Gauge
            gauge_placeholder.plotly_chart(
                render_gauge(new_score),
                use_container_width=True
            )

            # Status
            if new_score > 0.6:
                status_placeholder.markdown(
                    '<div class="status-danger">⚠ &nbsp; HIGH FRAUD RISK DETECTED</div>',
                    unsafe_allow_html=True
                )
            elif new_score > 0.3:
                status_placeholder.markdown(
                    '<div class="status-warning">⚡ &nbsp; SUSPICIOUS ACTIVITY</div>',
                    unsafe_allow_html=True
                )
            else:
                status_placeholder.markdown(
                    '<div class="status-safe">✓ &nbsp; CONVERSATION SAFE</div>',
                    unsafe_allow_html=True
                )

            # Transcript
            transcript_placeholder.markdown(f"""
            <div class='card card-orange'>
                <div class='section-title'>Latest Transcription</div>
                <div class='transcript-box'>{text}</div>
            </div>
            """, unsafe_allow_html=True)

            # Score details
            score_detail_placeholder.markdown(f"""
            <div style='font-family: Share Tech Mono, monospace; font-size: 0.8rem;
                        color: #444; text-align: center; letter-spacing: 1px;'>
                ML: {round(probability, 2)} &nbsp;|&nbsp;
                Keywords: {round(keyword_score, 2)} &nbsp;|&nbsp;
                Final: {round(new_score, 2)}
            </div>
            """, unsafe_allow_html=True)

            # Update metrics
            m1, m2, m3 = st.columns(3)
            # (metrics update on rerun naturally via session state)

        # Update history panel
        with right_col:
            render_history()

        time.sleep(0.5)