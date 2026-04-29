







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
import plotly.express as px
import time
import datetime

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="Scam Shield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------
# CSS
# ---------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    background-color: #06080f !important;
    color: #d0d8f0;
    font-family: 'Rajdhani', sans-serif;
}
.stApp {
    background: #06080f;
    background-image:
        radial-gradient(ellipse at 10% 10%, #1a000822 0%, transparent 50%),
        radial-gradient(ellipse at 90% 90%, #00102a22 0%, transparent 50%);
}
#MainMenu, footer, header { visibility: hidden; }

.main-header {
    text-align: center;
    padding: 10px 0 7px 0;
    border-bottom: 1px solid #cc000033;
    margin-bottom: 12px;
}
.main-header h1 {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.65rem;
    color: #cc0000;
    letter-spacing: 6px;
    text-shadow: 0 0 22px #cc000055;
    margin: 0;
}
.main-header .subtitle {
    color: #1e6fff;
    font-size: 0.65rem;
    letter-spacing: 4px;
    margin: 3px 0 0 0;
    text-transform: uppercase;
    opacity: 0.8;
}

/* Mic */
.mic-wrapper {
    display: flex; flex-direction: column;
    align-items: center; margin: 3px 0 4px 0;
}
.mic-btn {
    width: 58px; height: 58px; border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #120010, #06080f);
    border: 2px solid #441133;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 0 12px #33004422, inset 0 0 10px #00000088;
    cursor: default; transition: all 0.3s ease;
}
.mic-btn.active {
    border-color: #cc0000;
    box-shadow: 0 0 0 5px #cc000022, 0 0 0 11px #cc000011,
                0 0 26px #ff220055, inset 0 0 12px #00000088;
    animation: mic-pulse 1.2s ease-in-out infinite;
}
@keyframes mic-pulse {
    0%,100% { box-shadow: 0 0 0 5px #cc000033, 0 0 0 12px #cc000011, 0 0 26px #ff220044; }
    50%      { box-shadow: 0 0 0 9px #cc000055, 0 0 0 18px #cc000022, 0 0 42px #ff220088; }
}
.mic-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem; letter-spacing: 3px; color: #334455;
    margin-top: 4px; text-transform: uppercase;
}
.mic-label.active { color: #ff2200; }

/* Sound wave */
.soundwave {
    display: flex; align-items: center; gap: 3px;
    height: 26px; justify-content: center; margin: 2px auto 4px auto;
}
.soundwave .bar {
    width: 3px; border-radius: 2px;
    background: linear-gradient(to top, #cc0000, #1e6fff);
    animation: wave 0.9s ease-in-out infinite;
}
.soundwave .bar:nth-child(1){animation-delay:0.00s;height:6px}
.soundwave .bar:nth-child(2){animation-delay:0.10s;height:13px}
.soundwave .bar:nth-child(3){animation-delay:0.20s;height:20px}
.soundwave .bar:nth-child(4){animation-delay:0.30s;height:26px}
.soundwave .bar:nth-child(5){animation-delay:0.40s;height:17px}
.soundwave .bar:nth-child(6){animation-delay:0.30s;height:26px}
.soundwave .bar:nth-child(7){animation-delay:0.20s;height:20px}
.soundwave .bar:nth-child(8){animation-delay:0.10s;height:13px}
.soundwave .bar:nth-child(9){animation-delay:0.00s;height:6px}
@keyframes wave {
    0%,100%{transform:scaleY(0.25);opacity:0.4}
    50%{transform:scaleY(1);opacity:1}
}
.soundwave.idle .bar { height:4px !important; animation:none; opacity:0.15; }

/* Buttons */
div[data-testid="column"] .stButton > button {
    width: 100%; font-family: 'Share Tech Mono', monospace;
    letter-spacing: 2px; font-size: 0.8rem;
    height: 36px; border-radius: 6px; border: none;
    transition: all 0.2s ease;
}

/* Status */
.status-safe {
    background:#00100a; border:1px solid #00aa44; color:#00cc55;
    padding:6px 12px; border-radius:6px;
    font-family:'Share Tech Mono',monospace; font-size:0.85rem;
    text-align:center; letter-spacing:3px; text-shadow:0 0 8px #00cc5544;
}
.status-listening {
    background:#0a0014; border:1px solid #5533aa; color:#8866ee;
    padding:6px 12px; border-radius:6px;
    font-family:'Share Tech Mono',monospace; font-size:0.85rem;
    text-align:center; letter-spacing:3px;
}
.status-warning {
    background:#150800; border:1px solid #cc5500; color:#ff8800;
    padding:6px 12px; border-radius:6px;
    font-family:'Share Tech Mono',monospace; font-size:0.85rem;
    text-align:center; letter-spacing:3px; text-shadow:0 0 8px #cc550044;
}
.status-danger {
    background:#190000; border:1px solid #cc0000; color:#ff2200;
    padding:6px 12px; border-radius:6px;
    font-family:'Share Tech Mono',monospace; font-size:0.85rem;
    text-align:center; letter-spacing:3px;
    animation:pulse 1s infinite; text-shadow:0 0 10px #cc000066;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.55} }

/* Emotion badge */
.emotion-badge {
    display:inline-block; padding:3px 10px; border-radius:12px;
    font-family:'Share Tech Mono',monospace; font-size:0.72rem;
    letter-spacing:2px; margin:3px 3px 0 0;
}
.emo-fear    { background:#1a0022; border:1px solid #aa00ff; color:#cc66ff; }
.emo-anger   { background:#1a0000; border:1px solid #cc0000; color:#ff4444; }
.emo-urgency { background:#150800; border:1px solid #cc5500; color:#ff8800; }
.emo-coerce  { background:#001020; border:1px solid #0066aa; color:#3399ff; }
.emo-calm    { background:#001a08; border:1px solid #00aa44; color:#33cc66; }

/* Metrics */
.metric-box {
    background:#0b0e1a; border:1px solid #131827;
    border-radius:7px; padding:6px 4px; text-align:center;
}
.metric-label { font-size:0.55rem; color:#2a3044; letter-spacing:2px; text-transform:uppercase; margin-bottom:2px; }
.metric-value { font-family:'Share Tech Mono',monospace; font-size:1.15rem; color:#1e6fff; }
.metric-value.red   { color:#cc0000; }
.metric-value.green { color:#00cc55; }
.metric-value.orange{ color:#ff8800; }

/* Transcript */
.transcript-box {
    background:#080c15; border:1px solid #131827; border-radius:6px;
    padding:7px 11px; font-family:'Share Tech Mono',monospace;
    font-size:0.76rem; color:#7788aa;
    min-height:40px; max-height:68px; overflow-y:auto;
    line-height:1.5; word-break:break-word;
}
.section-title {
    font-family:'Share Tech Mono',monospace; font-size:0.58rem;
    color:#2a3044; letter-spacing:3px; text-transform:uppercase; margin-bottom:4px;
}

/* History */
.history-entry {
    background:#080c15; border:1px solid #0f1525;
    border-radius:5px; padding:6px 9px; margin-bottom:4px;
}
.history-time { font-family:'Share Tech Mono',monospace; font-size:0.58rem; color:#2a3044; margin-bottom:2px; }
.history-text { color:#7788aa; font-size:0.76rem; margin-bottom:2px; line-height:1.35; }
.safe-tag    { color:#00cc55; font-family:'Share Tech Mono',monospace; font-size:0.68rem; font-weight:bold; }
.warn-tag    { color:#ff8800; font-family:'Share Tech Mono',monospace; font-size:0.68rem; font-weight:bold; }
.danger-tag  { color:#cc0000; font-family:'Share Tech Mono',monospace; font-size:0.68rem; font-weight:bold; }

::-webkit-scrollbar { width:3px; }
::-webkit-scrollbar-track { background:#080c15; }
::-webkit-scrollbar-thumb { background:#cc0000; border-radius:2px; }
.js-plotly-plot { background:transparent !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Load Models
# ---------------------------
@st.cache_resource
def load_models():
    wm = whisper.load_model("small")
    m  = joblib.load("models/scam_model.pkl")
    v  = joblib.load("models/vectorizer.pkl")
    return wm, m, v

whisper_model, model, vectorizer = load_models()

# ---------------------------
# Keywords — English + Hinglish + Hindi
# ---------------------------
danger_keywords = [
    # English — authority
    "digital arrest","arrest","arrested","police","officer","inspector",
    "cyber crime","cybercrime","cbi","enforcement directorate","ed officer",
    "narcotics","customs officer","trai","telecom department",
    # English — investigation
    "investigation","fir","case registered","complaint filed",
    "fraud investigation","law enforcement","case number","inquiry",
    # English — financial coercion
    "money laundering","transfer money","send money","transfer funds",
    "wire transfer","frozen account","account blocked","account suspended",
    "financial crime","financial scrutiny","black money",
    # English — legal threats
    "legal action","warrant","arrest warrant","non-bailable",
    "legal consequences","court order","jail","prison","legal notice",
    # English — verification scams
    "verification","identity verification","aadhar verification",
    "pan verification","kyc verification","otp","share your otp",
    # English — secrecy/urgency
    "do not tell anyone","keep this confidential","do not inform",
    "within 24 hours","immediately","urgent","last warning",
    "cyber enforcement","fraud complaint","investigation officer",
    "screen share","stay on call","do not disconnect",

    # Hinglish / Hindi-English mix
    "digital giraftari","giraftari","girtaari",
    "aapko arrest kiya jayega","aap arrested hain",
    "aapka account freeze","account band ho jayega",
    "turant transfer karo","abhi paise bhejo",
    "aadhaar suspend","pan card block",
    "court order aaya hai","court ne order diya",
    "aapke upar fir darj","fir darj hogi",
    "kisi ko mat batao","kisi se baat mat karo",
    "24 ghante mein","abhi cooperate karo",
    "bail ke liye paise","fine bharna hoga",
    "non bailable warrant","giraftari ka warrant",
    "aapka number blacklist","number band hoga",
    "aapke naam pe case","case darj hai aapke",
    "cbi officer","cid officer","enforcement officer",
    "money laundering case","hawala ka case",
    "illegal transaction","suspicious transaction",
    "aap monitored hain","aap surveillance mein",
    "darr mat","ghabrana mat","yeh serious matter",
    "last chance hai","yeh aakhri mauka hai",
    "jail bheja jayega","prison mein jaoge",
    "aapki beti arrested","aapka beta case mein",
    "drug trafficking","drugs mila hai",
    "kisi ko inform mat karo","family ko mat batao",
]

HIGH_WEIGHT = {
    "digital arrest":0.40, "digital giraftari":0.40,
    "arrested":0.35, "aapko arrest kiya jayega":0.40,
    "arrest warrant":0.40, "giraftari ka warrant":0.40,
    "money laundering":0.35, "money laundering case":0.35,
    "do not tell anyone":0.40, "kisi ko mat batao":0.40,
    "keep this confidential":0.35, "kisi se baat mat karo":0.35,
    "frozen account":0.30, "aapka account freeze":0.30,
    "non-bailable":0.40, "non bailable warrant":0.40,
    "within 24 hours":0.25, "24 ghante mein":0.25,
    "transfer money":0.30, "abhi paise bhejo":0.30,
    "send money":0.30, "turant transfer karo":0.30,
    "wire transfer":0.30, "account blocked":0.28,
    "share your otp":0.45, "screen share":0.35,
    "drug trafficking":0.38, "drugs mila hai":0.35,
}

# ---------------------------
# Emotion Detection
# ---------------------------
EMOTION_PATTERNS = {
    "FEAR": {
        "keywords": ["scared","afraid","please don't","ghabrana","dar gaya","dar gayi",
                     "bachao","please help","mercy","begging","frighten"],
        "color": "emo-fear", "icon": "😨"
    },
    "ANGER": {
        "keywords": ["how dare","this is wrong","illegal","unfair","gussa","galat hai",
                     "yeh sahi nahi","protest","refuse","nahi maanunga"],
        "color": "emo-anger", "icon": "😠"
    },
    "URGENCY": {
        "keywords": ["immediately","right now","abhi","turant","urgent","jaldi",
                     "no time","last chance","aakhri mauka","within hours","within minutes"],
        "color": "emo-urgency", "icon": "⚡"
    },
    "COERCION": {
        "keywords": ["you must","you have to","aapko karna hoga","comply","mandatory",
                     "or else","warna","otherwise","no choice","forced"],
        "color": "emo-coerce", "icon": "🔒"
    },
    "CALM": {
        "keywords": ["relax","don't worry","safe","theek hai","koi baat nahi",
                     "all good","fine","no problem","sab theek"],
        "color": "emo-calm", "icon": "😌"
    },
}

def detect_emotions(text):
    text_l = text.lower()
    detected = []
    for emotion, data in EMOTION_PATTERNS.items():
        for kw in data["keywords"]:
            if kw in text_l:
                detected.append((emotion, data["color"], data["icon"]))
                break
    return detected

# ---------------------------
# Session State
# ---------------------------
defaults = {
    "running": False,
    "history": [],
    "current_score": 0.0,
    "total_chunks": 0,
    "high_risk_count": 0,
    "risk_timeline": [],       # list of (timestamp_str, score)
    "keyword_hit_count": 0,    # escalation memory counter
    "escalation_bonus": 0.0,   # accumulated escalation bonus
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------
# Header
# ---------------------------
st.markdown("""
<div class="main-header">
    <h1>🛡️ SCAM SHIELD</h1>
    <div class="subtitle">Real-Time Digital Arrest Scam Detection System</div>
</div>
""", unsafe_allow_html=True)

left_col, right_col = st.columns([3, 2], gap="large")

# ════════════════════════════════════════════
# LEFT COLUMN
# ════════════════════════════════════════════
with left_col:
    c1, c2 = st.columns(2)
    with c1:
        start_btn = st.button("▶  START MONITORING", type="primary", use_container_width=True)
    with c2:
        stop_btn  = st.button("📵  END CALL", type="secondary", use_container_width=True)

    if start_btn: st.session_state.running = True
    if stop_btn:
        st.session_state.running = False
        st.session_state.escalation_bonus = 0.0
        st.session_state.keyword_hit_count = 0
        st.session_state.current_score = 0.0

    mic_ph   = st.empty()
    wave_ph  = st.empty()

    def render_mic(active=False):
        cls  = "mic-btn active" if active else "mic-btn"
        lcls = "mic-label active" if active else "mic-label"
        mic_ph.markdown(
            f'<div class="mic-wrapper">'
            f'<div class="{cls}">🎙️</div>'
            f'<div class="{lcls}">{"LISTENING" if active else "READY"}</div>'
            f'</div>', unsafe_allow_html=True)

    def render_soundwave(active=False):
        cls = "soundwave" if active else "soundwave idle"
        wave_ph.markdown(
            f'<div class="{cls}">' + ''.join(['<div class="bar"></div>']*9) + '</div>',
            unsafe_allow_html=True)

    render_mic(False)
    render_soundwave(False)

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    mp = [m1.empty(), m2.empty(), m3.empty(), m4.empty()]

    def render_metrics():
        sp = int(st.session_state.current_score * 100)
        sc = "red" if sp > 60 else ("orange" if sp > 30 else "green")
        rc = "red" if st.session_state.high_risk_count > 0 else "green"
        eb = int(st.session_state.escalation_bonus * 100)
        ec = "red" if eb > 20 else "orange" if eb > 10 else "green"
        mp[0].markdown(f'<div class="metric-box"><div class="metric-label">Chunks</div><div class="metric-value">{st.session_state.total_chunks}</div></div>', unsafe_allow_html=True)
        mp[1].markdown(f'<div class="metric-box"><div class="metric-label">High Risk</div><div class="metric-value {rc}">{st.session_state.high_risk_count}</div></div>', unsafe_allow_html=True)
        mp[2].markdown(f'<div class="metric-box"><div class="metric-label">Risk %</div><div class="metric-value {sc}">{sp}%</div></div>', unsafe_allow_html=True)
        mp[3].markdown(f'<div class="metric-box"><div class="metric-label">Escalation</div><div class="metric-value {ec}">+{eb}%</div></div>', unsafe_allow_html=True)

    render_metrics()

    gauge_ph      = st.empty()
    status_ph     = st.empty()
    emotion_ph    = st.empty()
    transcript_ph = st.empty()
    detail_ph     = st.empty()
    timeline_ph   = st.empty()

    # ── Gauge ──
    def render_gauge(score):
        val = score * 100
        if val > 60:
            bc, nc = "#cc0000", "#ff2200"
            steps = [('#001a06',0,30),('#1a0c00',30,60),('#2a0000',60,100)]
        elif val > 30:
            bc, nc = "#cc6600", "#ff8800"
            steps = [('#001a06',0,30),('#1a0c00',30,60),('#1a0000',60,100)]
        else:
            bc, nc = "#00aa44", "#00cc55"
            steps = [('#001a06',0,30),('#0a1a00',30,60),('#180000',60,100)]

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            number={'suffix':"%",'font':{'color':bc,'size':24,'family':'Share Tech Mono'}},
            title={'text':"FRAUD RISK",'font':{'color':'#2a3044','size':9,'family':'Share Tech Mono'}},
            gauge={
                'axis':{'range':[0,100],'tickcolor':'#131827',
                        'tickfont':{'color':'#2a3044','size':8},'tickwidth':1},
                'bar':{'color':bc,'thickness':0.2},
                'bgcolor':'#0b0e1a','borderwidth':0,
                'steps':[{'range':[s[1],s[2]],'color':s[0]} for s in steps],
                'threshold':{'line':{'color':nc,'width':3},'thickness':0.8,'value':val}
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font={'color':'#d0d8f0'}, height=190,
            margin=dict(t=26, b=4, l=10, r=10)
        )
        return fig

    # ── Risk Timeline ──
    def render_timeline():
        tl = st.session_state.risk_timeline
        if len(tl) < 2:
            timeline_ph.markdown(
                '<div class="section-title" style="margin-top:5px;">📈 RISK ESCALATION TIMELINE</div>'
                '<div style="color:#2a3044;font-family:Share Tech Mono,monospace;'
                'font-size:0.65rem;text-align:center;padding:10px 0;">AWAITING DATA...</div>',
                unsafe_allow_html=True)
            return

        times  = [t[0] for t in tl]
        scores = [t[1]*100 for t in tl]
        colors = ["#cc0000" if s > 60 else "#ff8800" if s > 30 else "#00cc55" for s in scores]

        fig = go.Figure()
        # Shaded zones
        fig.add_hrect(y0=0,  y1=30,  fillcolor="#00cc5511", line_width=0)
        fig.add_hrect(y0=30, y1=60,  fillcolor="#ff880011", line_width=0)
        fig.add_hrect(y0=60, y1=100, fillcolor="#cc000011", line_width=0)
        # Line
        fig.add_trace(go.Scatter(
            x=times, y=scores,
            mode='lines+markers',
            line=dict(color='#1e6fff', width=2),
            marker=dict(color=colors, size=7, line=dict(color='#06080f', width=1)),
            fill='tozeroy',
            fillcolor='rgba(30,111,255,0.07)'
        ))
        # Threshold lines
        fig.add_hline(y=30, line=dict(color="#ff880033", width=1, dash="dot"))
        fig.add_hline(y=60, line=dict(color="#cc000033", width=1, dash="dot"))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=130,
            margin=dict(t=8, b=22, l=30, r=10),
            xaxis=dict(showgrid=False, tickfont=dict(color='#2a3044', size=8),
                       tickangle=-30, color='#2a3044'),
            yaxis=dict(showgrid=False, range=[0,100],
                       tickfont=dict(color='#2a3044', size=8),
                       tickvals=[0,30,60,100], color='#2a3044'),
            showlegend=False
        )
        timeline_ph.markdown(
            '<div class="section-title" style="margin-top:5px;">📈 RISK ESCALATION TIMELINE</div>',
            unsafe_allow_html=True)
        timeline_ph.plotly_chart(fig, use_container_width=True)

    # Initial state
    gauge_ph.plotly_chart(render_gauge(0), use_container_width=True)
    status_ph.markdown('<div class="status-safe">⬤ &nbsp; SYSTEM READY</div>', unsafe_allow_html=True)
    emotion_ph.markdown("", unsafe_allow_html=True)
    transcript_ph.markdown(
        '<div class="section-title" style="margin-top:4px;">📝 LATEST TRANSCRIPTION</div>'
        '<div class="transcript-box">Waiting for audio input...</div>',
        unsafe_allow_html=True)
    render_timeline()

# ════════════════════════════════════════════
# RIGHT COLUMN — Call Log
# ════════════════════════════════════════════
with right_col:
    st.markdown('<div class="section-title" style="margin-bottom:8px;">📋 &nbsp; CALL LOG</div>',
                unsafe_allow_html=True)
    history_ph = st.empty()

    def render_history():
        if not st.session_state.history:
            history_ph.markdown(
                '<div style="color:#1a2030;font-family:Share Tech Mono,monospace;'
                'font-size:0.68rem;letter-spacing:2px;text-align:center;padding:22px 0;">'
                'NO ENTRIES YET</div>', unsafe_allow_html=True)
        else:
            html = ""
            for e in reversed(st.session_state.history[-20:]):
                sp = int(e['score'] * 100)
                if e['score'] > 0.6:
                    tc, badge = "danger-tag", f"⚠ HIGH RISK — {sp}%"
                elif e['score'] > 0.3:
                    tc, badge = "warn-tag",   f"⚡ SUSPICIOUS — {sp}%"
                else:
                    tc, badge = "safe-tag",   f"✓ SAFE — {sp}%"

                kws = [k for k in danger_keywords if k in e['text'].lower()]
                kw_html = (
                    f'<div style="font-size:0.62rem;color:#aa0033;margin-top:2px;">'
                    f'🔑 {", ".join(kws[:4])}</div>'
                ) if kws else ""

                emo_html = ""
                for emo, ecls, eico in e.get('emotions', []):
                    emo_html += f'<span class="emotion-badge {ecls}">{eico} {emo}</span>'

                safe_text = e['text'][:150] + ('...' if len(e['text']) > 150 else '')
                html += (
                    '<div class="history-entry">'
                    f'<div class="history-time">{e["time"]}</div>'
                    f'<div class="history-text">{safe_text}</div>'
                    f'{kw_html}{emo_html}'
                    f'<div class="{tc}">{badge}</div>'
                    '</div>'
                )
            history_ph.markdown(html, unsafe_allow_html=True)

    render_history()

# ════════════════════════════════════════════
# DETECTION LOOP
# ════════════════════════════════════════════
if st.session_state.running:
    duration    = 8
    sample_rate = 16000

    while st.session_state.running:
        render_mic(True)
        render_soundwave(True)
        status_ph.markdown(
            '<div class="status-listening">◉ &nbsp; LISTENING...</div>',
            unsafe_allow_html=True)

        audio = sd.rec(int(duration * sample_rate),
                       samplerate=sample_rate, channels=1, dtype='float32')
        sd.wait()
        audio = np.squeeze(audio)
        write("temp.wav", sample_rate, audio)
        render_soundwave(False)

        result = whisper_model.transcribe(
            "temp.wav", fp16=False, language=None,   # None = auto-detect language incl. Hindi
            condition_on_previous_text=False, temperature=0.0
        )
        text = result["text"].strip()

        if not text:
            render_mic(False)
            status_ph.markdown(
                '<div class="status-safe">🔇 &nbsp; NO SPEECH DETECTED</div>',
                unsafe_allow_html=True)
            time.sleep(1)
            continue

        # ── ML Prediction ──
        text_vec    = vectorizer.transform([text])
        probability = model.predict_proba(text_vec)[0][1]

        # ── Weighted Keyword Scoring ──
        text_lower    = text.lower()
        keyword_score = 0.0
        hits_this_chunk = 0
        for word in danger_keywords:
            if word in text_lower:
                keyword_score += HIGH_WEIGHT.get(word, 0.15)
                hits_this_chunk += 1
        keyword_score = min(keyword_score, 0.6)

        # ── Escalation Memory ──
        # Each chunk with 2+ keyword hits adds to escalation bonus
        if hits_this_chunk >= 2:
            st.session_state.keyword_hit_count += hits_this_chunk
            st.session_state.escalation_bonus = min(
                st.session_state.escalation_bonus + 0.05 * hits_this_chunk, 0.4
            )
        else:
            # Slowly decay escalation if no hits
            st.session_state.escalation_bonus = max(
                st.session_state.escalation_bonus - 0.02, 0.0
            )

        # ── Final Score ──
        raw_score = min(probability + keyword_score + st.session_state.escalation_bonus, 1.0)
        prev      = st.session_state.current_score
        new_score = prev + (raw_score - prev) * (0.8 if raw_score > prev else 0.3)
        st.session_state.current_score = new_score
        st.session_state.total_chunks += 1
        if new_score > 0.6:
            st.session_state.high_risk_count += 1

        # ── Emotion Detection ──
        emotions = detect_emotions(text)

        # ── Save to history ──
        st.session_state.history.append({
            'time':    datetime.datetime.now().strftime("%H:%M:%S"),
            'text':    text,
            'score':   new_score,
            'ml':      probability,
            'keywords':keyword_score,
            'emotions':emotions,
        })

        # ── Save to timeline ──
        st.session_state.risk_timeline.append((
            datetime.datetime.now().strftime("%H:%M:%S"),
            new_score
        ))

        # ── Update UI ──
        gauge_ph.plotly_chart(render_gauge(new_score), use_container_width=True)

        if new_score > 0.6:
            status_ph.markdown(
                '<div class="status-danger">⚠ &nbsp; HIGH FRAUD RISK DETECTED</div>',
                unsafe_allow_html=True)
        elif new_score > 0.3:
            status_ph.markdown(
                '<div class="status-warning">⚡ &nbsp; SUSPICIOUS ACTIVITY</div>',
                unsafe_allow_html=True)
        else:
            status_ph.markdown(
                '<div class="status-safe">✓ &nbsp; CONVERSATION SAFE</div>',
                unsafe_allow_html=True)

        render_mic(new_score > 0.3)

        # Emotion badges
        if emotions:
            badges = "".join(
                f'<span class="emotion-badge {ecls}">{eico} {emo}</span>'
                for emo, ecls, eico in emotions
            )
            emotion_ph.markdown(
                f'<div style="margin:3px 0 4px 0;">{badges}</div>',
                unsafe_allow_html=True)
        else:
            emotion_ph.markdown("", unsafe_allow_html=True)

        transcript_ph.markdown(
            '<div class="section-title" style="margin-top:4px;">📝 LATEST TRANSCRIPTION</div>'
            f'<div class="transcript-box">{text}</div>',
            unsafe_allow_html=True)

        detail_ph.markdown(
            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.65rem;'
            f'color:#2a3044;text-align:center;letter-spacing:1px;margin-top:2px;">'
            f'ML:{round(probability,2)} | KW:{round(keyword_score,2)} '
            f'| ESC:+{round(st.session_state.escalation_bonus,2)} '
            f'| Final:{round(new_score,2)}</div>',
            unsafe_allow_html=True)

        render_metrics()
        render_timeline()

        with right_col:
            render_history()

        time.sleep(0.5)