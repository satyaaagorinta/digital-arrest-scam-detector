import streamlit as st
from faster_whisper import WhisperModel
import joblib
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import plotly.graph_objects as go
import datetime
from scipy.sparse import hstack, csr_matrix
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from predict_conversation import ConversationPredictor
    CONV_MODEL_AVAILABLE = True
except Exception:
    CONV_MODEL_AVAILABLE = False


# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Scam Shield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ══════════════════════════════════════════════════════════════
# SESSION STATE — initialize FIRST, before any widget or column
# This is the #1 fix: all keys guarded with `if k not in`,
# so reruns NEVER wipe existing data.
# ══════════════════════════════════════════════════════════════
def _fresh_state():
    # Returns NEW list instances every call — avoids mutable default sharing bug
    return {
        "history":                 [],
        "conversation":            [],
        "risk_timeline":           [],
        "current_score":           0.0,
        "total_chunks":            0,
        "high_risk_count":         0,
        "escalation_bonus":        0.0,
        "keyword_hit_count":       0,
        "transcript_window":       [],
        "last_attacker_score":     0.0,
        "last_attacker_groups":    [],
        "consecutive_compliances": 0,
        "final_analysis_done":     False,
        "final_result":            None,
        "last_attacker_chunk":     None,
        "last_victim_chunk":       None,
        "warning_msg":             None,
        "status_msg":              None,
    }

for k, v in _fresh_state().items():
    if k not in st.session_state:
        st.session_state[k] = v
st.sidebar.write(f"DEBUG: conv={len(st.session_state.conversation)} | status={st.session_state.status_msg}")


# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
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
div[data-testid="column"] .stButton > button {
    width: 100%; font-family: 'Share Tech Mono', monospace;
    letter-spacing: 2px; font-size: 0.8rem;
    height: 36px; border-radius: 6px; border: none;
    transition: all 0.2s ease;
}
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
.metric-box {
    background:#0b0e1a; border:1px solid #131827;
    border-radius:7px; padding:6px 4px; text-align:center;
}
.metric-label { font-size:0.55rem; color:#2a3044; letter-spacing:2px; text-transform:uppercase; margin-bottom:2px; }
.metric-value { font-family:'Share Tech Mono',monospace; font-size:1.15rem; color:#1e6fff; }
.metric-value.red   { color:#cc0000; }
.metric-value.green { color:#00cc55; }
.metric-value.orange{ color:#ff8800; }
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


# ══════════════════════════════════════════════════════════════
# LOAD MODELS
# ══════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_models():
    wm = WhisperModel("base", device="cpu", compute_type="int8")
    m  = joblib.load("models/scam_model.pkl")
    v  = joblib.load("models/vectorizer.pkl")
    return wm, m, v

whisper_model, model, vectorizer = load_models()


# ══════════════════════════════════════════════════════════════
# CIALDINI GROUPS
# ══════════════════════════════════════════════════════════════
CIALDINI_GROUPS = {
    "authority": {
        "score": 0.30,
        "keywords": [
            "cbi officer","cyber crime department","enforcement directorate",
            "income tax officer","trai officer","rbi officer","narcotics",
            "anti terrorism squad","national investigation agency",
            "financial intelligence unit","economic offences wing",
            "serious fraud investigation office","sebi officer",
            "ministry of home affairs","supreme court","high court",
            "sessions court","magistrate","central vigilance commission",
            "inspector general","deputy commissioner","superintendent of police",
            "cid officer","joint director","directorate of revenue intelligence",
            "sfio","lokayukta","lokpal","cert-in","intelligence bureau",
            "national crime records bureau","interpol","ed officer",
            "anti corruption bureau","election commission","dcp",
            "nia officer","crime branch","vigilance officer","police officer",
            "government officer","court appointed","judicial officer",
            "senior officer","investigation officer","cyber cell",
            "national cyber crime","treasury officer",
            "jaanch adhikaari","sarkaari adhikaari","vibhaag se",
            "cbi se hain","police vibhaag","court ka order",
        ]
    },
    "urgency": {
        "score": 0.30,
        "keywords": [
            "within 24 hours","immediately","right now","last chance",
            "final notice","last warning","within 2 hours","60 minutes",
            "30 minutes","45 minutes","tonight","today only",
            "no time left","before midnight","by end of day",
            "abhi","turant","abhi ke abhi","24 ghante mein",
            "ek ghante mein","2 ghante mein","aaj raat tak",
            "aaj tak","jaldi karo","der mat karo","aakhri mauka",
            "last date","deadline","act now","do not delay",
            "final opportunity","last moment","running out of time",
        ]
    },
    "scarcity": {
        "score": 0.25,
        "keywords": [
            "one time settlement","one time waiver","limited time offer",
            "only chance","cannot be extended","no second chance",
            "this offer expires","rare opportunity","special window",
            "last opportunity","after this call","ek baar ka mauka",
            "yeh mauka nahi milega","aakhri baar","ab nahi hoga",
            "sirf aaj","only today","out of court settle",
            "settlement window","after today no help",
            "cannot help after this","government scheme aaj tak",
        ]
    },
    "warrant": {
        "score": 0.25,
        "keywords": [
            "arrest warrant","non-bailable warrant","look-out notice",
            "court order","fir registered","fir darj","legal notice",
            "summons","court summons","attachment order","seizure order",
            "warrant execute","warrant issued","bailable warrant",
            "anticipatory bail","preventive detention","section 420",
            "pmla","fema violation","ipc section","contempt of court",
            "sub judice","ex-parte order","charge sheet","bail rejected",
            "giraftaari ka warrant","court notice","girtaari ka aadesh",
            "non bailable","warrant aayega","notice aayega",
        ]
    },
    "money": {
        "score": 0.30,
        "keywords": [
            "transfer money","send money","pay immediately","transfer funds",
            "wire transfer","pay fine","security deposit","processing fee",
            "verification fee","settlement amount","clearance fee",
            "pay the penalty","pay or face","deposit amount",
            "escrow account","secret account","government account",
            "paise transfer karo","abhi paise bhejo","turant transfer",
            "fine bharo","fees bharo","payment karo","jama karo",
            "amount bhejo","rupees transfer","lakh transfer",
            "hawala payment","cash deposit","online payment karo",
            "neft karo","rtgs karo","upi se bhejo",
        ]
    },
    "reciprocity": {
        "score": 0.20,
        "keywords": [
            "we are trying to help you","we want to protect you",
            "i am on your side","we are your well-wishers",
            "helping you out","doing you a favour","personally ensuring",
            "i will personally","guarantee your safety","protect your family",
            "immunity from prosecution","clean chit guarantee",
            "case close karenge","aapko bachayenge","aapki help kar rahe hain",
            "aapke saath hain","aapka bhala chahte hain",
            "personally handle karunga","sifarish karenge",
            "leniency dilaayenge","aapko protect karenge",
            "hum guarantee dete hain","aapke liye kuch kar sakte hain",
        ]
    },
    "threat": {
        "score": 0.30,
        "keywords": [
            "face arrest","you will be arrested","arrested tonight",
            "jail bheja jayega","prison mein jaoge","aapko pakad lenge",
            "raid padegi","police aayegi","officer aa raha hai",
            "property seized","assets frozen","account blocked",
            "media mein aayega","employer ko batayenge","family ko involve",
            "aapki beti arrested","aapka beta case mein","family member named",
            "reputation destroy","public embarrassment","nationwide notice",
            "travel ban","passport blacklisted","criminal record",
            "dhamki","khatre mein","consequences severe",
            "will not be able to help","cannot save you after this",
        ]
    },
    "account": {
        "score": 0.20,
        "keywords": [
            "share your otp","otp batao","account number share",
            "net banking credentials","atm card number","cvv number",
            "pin number","share bank details","verify account",
            "aadhaar number share","pan number verify","account verification",
            "kyc update","kyc verify karo","biometric verify",
            "screen share karo","remote access","aadhar otp share",
            "netbanking username","password share","login details",
            "account details share","banking details","debit card details",
            "credit card number","ifsc share","account froze",
            "account suspend","aapka account block","frozen account",
        ]
    },
    "distraction": {
        "score": 0.25,
        "keywords": [
            "sealed case","confidential investigation","classified matter",
            "do not tell anyone","don't inform your family","keep this secret",
            "top secret","classified operation","confidential case",
            "kisi ko mat batana","ghar mein mat batana","secret rakhna",
            "apne parivar ko mat batao","do not call anyone",
            "stay on the line","do not disconnect","line mat kaatna",
            "phone mat rakhna","apne lawyer ko mat bulao",
            "this is classified","classified inquiry","internal matter",
        ]
    },
}

GENERIC_ONLY_GROUPS = {
    "urgency": {
        "tonight","today only","act now","do not delay",
        "final opportunity","last moment","running out of time",
        "deadline","last date",
    },
}

COMBINATIONS = [
    {"groups": ["authority", "warrant"],            "bonus": 0.15},
    {"groups": ["authority", "threat"],             "bonus": 0.15},
    {"groups": ["urgency",   "money"],              "bonus": 0.12},
    {"groups": ["urgency",   "threat"],             "bonus": 0.12},
    {"groups": ["scarcity",  "money"],              "bonus": 0.10},
    {"groups": ["authority", "money"],              "bonus": 0.12},
    {"groups": ["warrant",   "money"],              "bonus": 0.13},
    {"groups": ["threat",    "money"],              "bonus": 0.14},
    {"groups": ["distraction","authority"],         "bonus": 0.10},
    {"groups": ["authority", "warrant", "urgency"], "bonus": 0.20},
    {"groups": ["authority", "threat",  "money"],   "bonus": 0.22},
    {"groups": ["account",   "urgency"],            "bonus": 0.15},
    {"groups": ["account",   "authority"],          "bonus": 0.15},
]

SAFE_CONTEXT = {
    "hello","hi","hey","okay","ok","yes","no","please","thank","thanks",
    "sure","alright","right","correct","understood","noted","got","good",
    "fine","great","nice","welcome","bye","goodbye","see","later","talk",
    "speak","call","calling","called","back","again","one","moment","second",
    "minute","wait","hold","please","hold on","just","checking","verify",
    "name","your","my","our","this","that","with","from","have","will",
    "can","you","me","we","they","i","is","are","was","were","be","been",
    "do","does","did","get","got","give","take","make","let","know",
    "think","want","need","like","would","could","should","may","might",
    "dear","sir","ma'am","madam","respected","greetings",
    "haan","nahi","theek","ji","aap","main","hum","kya","hai","tha","thi",
    "karo","karna","baat","samajh","shukriya","dhanyavaad","namaste",
    "urgent call","join the call","hop on a call","quick call",
    "send report","submit report","urgent deadline","project deadline",
    "urgent update","status update","send update","share update",
    "urgent request","please send","please share","can you send",
    "send me","share the","please upload","upload the file",
    "urgent task","priority task","high priority","top priority",
    "immediate action","action required","response needed",
    "reply urgently","respond asap","get back to me","follow up",
    "quick update","brief update","daily update","weekly update",
    "team meeting","board meeting","client meeting","sync up",
    "let us sync","quick sync","touch base","catch up",
}

MIN_CONFIDENCE = 0.35
MIN_TEXT_LEN   = 4

NEGATION_PHRASES = {
    "just joking","just kidding","i'm joking","i am joking","i'm kidding",
    "i am kidding","just a joke","only joking","only kidding","it's a prank",
    "its a prank","just playing","i was joking","i was kidding",
    "haha","lol","lmao","just messing","just testing",
    "mazak kar raha","mazak tha","joke kar raha","bas mazak",
    "kidding yaar","joking yaar","timepass","fun mein bola",
}

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

VICTIM_RESPONSE_SIGNALS = {
    "deference": {
        "phrases": [
            "yes sir","yes officer","yes ma'am","okay sir","ji haan","haan sir",
            "ji officer","samajh gaya","theek hai sir","ji bilkul","zaroor sir",
            "as you say","i understand officer","whatever you say","i'll cooperate",
            "i will cooperate","cooperate karunga","cooperate karenge",
            "aap sahi keh rahe","mujhe maafi","i'm sorry sir","of course officer",
        ],
        "base_weight": 0.45,
        "triggered_by": ["authority","warrant"],
    },
    "panic": {
        "phrases": [
            "okay okay","what do i do","what should i do","kya karun","kya karoon",
            "please help","tell me what to do","jaldi batao","abhi kya karun",
            "i'll do it","kar deta hoon","kar deti hoon","yes yes",
            "okay i'm doing it","i'm transferring","sending now","bhej raha hoon",
            "please don't arrest","ghabra gaya","ghabra gayi","i'm scared",
            "dar lag raha","please don't","mujhe kya karna","i'm confused",
        ],
        "base_weight": 0.40,
        "triggered_by": ["urgency","scarcity","threat"],
    },
    "obligatory": {
        "phrases": [
            "thank you for telling me","thank you for informing","thanks for warning",
            "i appreciate","batane ke liye shukriya","shukriya","dhanyavaad",
            "you're helping me","i know you're trying to help","i'll do as you say",
            "aap ne bataya isliye","aapka shukriya","aap sahi keh rahe hain",
        ],
        "base_weight": 0.30,
        "triggered_by": ["reciprocity"],
    },
    "consistency": {
        "phrases": [
            "i said i would","i already said","maine kaha tha","haan maine kaha",
            "i'm not going back","i'll keep my word","i said yes","i agreed",
            "yes i'll do it","i won't back out","as i said","jaise maine kaha",
        ],
        "base_weight": 0.25,
        "triggered_by": ["commitment"],
    },
    "info_leak": {
        "phrases": [
            "my account number","my otp is","my pin is","my card number",
            "cvv is","aadhaar is","pan number","date of birth is",
            "otp aaya","otp share","pin batata","mera account number",
            "mera otp","meri id","card number hai","details de deta",
            "password","net banking","login id","user id","my address is",
        ],
        "base_weight": 0.70,
        "triggered_by": ["account","authority","urgency"],
    },
    "resistance": {
        "phrases": [
            "no","i won't","i refuse","this is a scam","you are a fraud",
            "i'm calling police","calling my lawyer","i don't believe you",
            "nahi karunga","nahi karungi","fraud hai","scam hai",
            "police bulata hoon","fake call","i'm hanging up","who are you really",
            "prove it","show me your id","i need proof","verify yourself",
            "mujhe nahi karna","jhooth bol rahe","aap fraud hain",
        ],
        "base_weight": -0.40,
        "triggered_by": [],
    },
}

PRINCIPLE_AMPLIFIERS = {
    ("authority",   "deference"):   1.4,
    ("urgency",     "panic"):       1.3,
    ("scarcity",    "panic"):       1.2,
    ("reciprocity", "obligatory"):  1.3,
    ("commitment",  "consistency"): 1.2,
    ("threat",      "panic"):       1.35,
    ("money",       "info_leak"):   1.5,
    ("account",     "info_leak"):   1.6,
}


# ══════════════════════════════════════════════════════════════
# PURE SCORING FUNCTIONS
# ══════════════════════════════════════════════════════════════

def is_safe_context(text):
    text = text.strip()
    if len(text) < MIN_TEXT_LEN:
        return True
    words = set(text.lower().split())
    if words.issubset(SAFE_CONTEXT):
        return True
    if len(words) <= 5 and len(words & SAFE_CONTEXT) / max(len(words), 1) >= 0.7:
        return True
    return False

def compute_keyword_score(text):
    text_lower = text.lower()
    groups_hit = set()
    for group_name, group_data in CIALDINI_GROUPS.items():
        for kw in group_data["keywords"]:
            if kw in text_lower:
                groups_hit.add(group_name)
                break
    if len(groups_hit) < 2:
        return 0.0, groups_hit, None
    non_generic = groups_hit - set(GENERIC_ONLY_GROUPS.keys())
    adjusted_groups = set()
    for gname in groups_hit:
        if gname in GENERIC_ONLY_GROUPS:
            hit_kw = next((kw for kw in CIALDINI_GROUPS[gname]["keywords"] if kw in text_lower), None)
            if hit_kw in GENERIC_ONLY_GROUPS[gname]:
                if len(non_generic) >= 1:
                    adjusted_groups.add(gname)
            else:
                adjusted_groups.add(gname)
        else:
            adjusted_groups.add(gname)
    if len(adjusted_groups) < 2:
        return 0.0, adjusted_groups, None
    base_score = sum(CIALDINI_GROUPS[g]["score"] for g in adjusted_groups)
    combo_bonus, combo_name = 0.0, None
    for combo in COMBINATIONS:
        if set(combo["groups"]).issubset(adjusted_groups):
            if combo["bonus"] > combo_bonus:
                combo_bonus = combo["bonus"]
                combo_name  = "+".join(combo["groups"])
    return min(base_score + combo_bonus, 1.0), adjusted_groups, combo_name

def get_context_text(new_text, window, max_window=2):
    window.append(new_text)
    if len(window) > max_window:
        window.pop(0)
    return " ".join(window)

def detect_emotions(text):
    text_l = text.lower()
    detected = []
    for emotion, data in EMOTION_PATTERNS.items():
        for kw in data["keywords"]:
            if kw in text_l:
                detected.append((emotion, data["color"], data["icon"]))
                break
    return detected

def score_victim_response(victim_text, attacker_groups_hit, last_attacker_score):
    if not victim_text or not victim_text.strip():
        return 0.0, "neutral"
    text_lower = victim_text.lower()
    best_score, best_type = 0.0, "neutral"
    for response_type, data in VICTIM_RESPONSE_SIGNALS.items():
        for phrase in data["phrases"]:
            if phrase in text_lower:
                raw_weight = data["base_weight"]
                amplifier  = 1.0
                for attacker_group in attacker_groups_hit:
                    key = (attacker_group, response_type)
                    if key in PRINCIPLE_AMPLIFIERS:
                        amplifier = max(amplifier, PRINCIPLE_AMPLIFIERS[key])
                weighted = raw_weight * amplifier
                if last_attacker_score > 0.6:
                    weighted *= 1.3
                elif last_attacker_score > 0.38:
                    weighted *= 1.1
                if abs(weighted) > abs(best_score):
                    best_score = weighted
                    best_type  = response_type
                break
    return round(min(max(best_score, -1.0), 1.0), 3), best_type

def analyse_full_conversation(conversation):
    from collections import Counter
    if not conversation:
        return None
    attacker_turns = [t for t in conversation if t["speaker"] == "attacker"]
    victim_turns   = [t for t in conversation if t["speaker"] == "victim"]
    if not attacker_turns:
        return None
    attacker_scores   = [t["score"] for t in attacker_turns]
    avg_attacker      = sum(attacker_scores) / len(attacker_scores)
    peak_attacker     = max(attacker_scores)
    compliance_scores = [t.get("compliance_score", 0.0) for t in victim_turns]
    if compliance_scores:
        avg_compliance = sum(compliance_scores) / len(compliance_scores)
        if len(compliance_scores) >= 3:
            mid = len(compliance_scores) // 2
            trajectory_bonus = (sum(compliance_scores[mid:])/len(compliance_scores[mid:])
                              - sum(compliance_scores[:mid])/len(compliance_scores[:mid])) * 0.15
        else:
            trajectory_bonus = 0.0
    else:
        avg_compliance, trajectory_bonus = 0.0, 0.0
    max_consecutive = current_streak = 0
    for t in victim_turns:
        if t.get("compliance_score", 0) > 0.15:
            current_streak += 1
            max_consecutive = max(max_consecutive, current_streak)
        else:
            current_streak = 0
    info_disclosed     = any(t.get("response_type") == "info_leak" for t in victim_turns)
    critical_bonus     = 0.35 if info_disclosed else 0.0
    resistance_count   = sum(1 for t in victim_turns if t.get("response_type") == "resistance")
    resistance_penalty = min(resistance_count * 0.10, 0.25)
    raw = (
        0.40 * avg_attacker
        + 0.35 * max(avg_compliance, 0)
        + 0.10 * min(max_consecutive * 0.08, 0.30)
        + 0.15 * (peak_attacker * 0.5 + critical_bonus * 0.5)
        + trajectory_bonus - resistance_penalty
    )
    final_score = round(min(max(raw, 0.0), 1.0), 3)
    if info_disclosed:
        verdict, color = "CRITICAL — Information Disclosed", "#cc0000"
    elif final_score > 0.65:
        verdict, color = "HIGH FRAUD RISK", "#cc0000"
    elif final_score > 0.40:
        verdict, color = "SUSPICIOUS CONVERSATION", "#ff8800"
    elif final_score > 0.20:
        verdict, color = "LOW RISK — Monitor", "#ffcc00"
    else:
        verdict, color = "SAFE CONVERSATION", "#00cc55"
    all_groups = []
    for t in attacker_turns:
        all_groups.extend(list(t.get("groups", [])))
    dominant = [g for g, _ in Counter(all_groups).most_common(3)]
    return {
        "final_score": final_score, "verdict": verdict, "color": color,
        "avg_attacker": round(avg_attacker, 3),
        "peak_attacker": round(peak_attacker, 3),
        "avg_compliance": round(avg_compliance, 3),
        "info_disclosed": info_disclosed,
        "dominant_principles": dominant,
        "resistance_count": resistance_count,
        "num_principles": len(set(all_groups)),
        "attacker_turns": len(attacker_turns),
        "victim_turns": len(victim_turns),
    }


# ══════════════════════════════════════════════════════════════
# AUDIO + TRANSCRIPTION
# ══════════════════════════════════════════════════════════════
# @st.cache_resource(show_spinner=False)
# def load_models():
#     wm = WhisperModel("base", device="cpu", compute_type="int8")
#     m  = joblib.load("models/scam_model.pkl")
#     v  = joblib.load("models/vectorizer.pkl")
#     return wm, m, v

# whisper_model, model, vectorizer = load_models()


def record_and_transcribe(duration=8):
    wav_path    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp.wav")
    native_rate = 44100   # Intel Array native rate
    target_rate = 16000   # Whisper expects 16kHz

    # Record at native rate
    audio = sd.rec(int(duration * native_rate), samplerate=native_rate,
                   channels=1, dtype='float32')
    sd.wait()
    audio = np.squeeze(audio)

    if audio is None or len(audio) == 0:
        return None

    max_amp = float(np.max(np.abs(audio)))
    if max_amp < 0.0001:
        return None

    # Normalize to boost quiet mic
    audio = (audio / max_amp * 0.95).astype(np.float32)

    # Resample 44100 → 16000
    from scipy.signal import resample
    num_samples = int(len(audio) * target_rate / native_rate)
    audio = resample(audio, num_samples).astype(np.float32)

    # Write at 16000 for Whisper
    write(wav_path, target_rate, audio)

    segments, info = whisper_model.transcribe(
        wav_path,
        beam_size=5,
        vad_filter=False,
        language="en",
        condition_on_previous_text=False,
    )
    text = " ".join([seg.text for seg in segments]).strip()

    HALLUCINATIONS = {"thank you", "thanks for watching", "bye", "you", ".", "...", " "}
    if text.lower().strip() in HALLUCINATIONS:
        return None
    return text if text and len(text.strip()) >= 2 else None


# ══════════════════════════════════════════════════════════════
# CHUNK PROCESSORS  — write to session_state, return nothing.
# Called only from button handlers, never from render code.
# ══════════════════════════════════════════════════════════════
def process_attacker_chunk(text):
    
    now = datetime.datetime.now().strftime("%H:%M:%S")
    if is_safe_context(text):
        new_score = st.session_state.current_score * 0.4
        entry = {
            "speaker": "attacker", "time": now, "text": text,
            "score": new_score, "ml": 0.0, "keywords": 0.0,
            "groups": [], "combo": None, "emotions": [],
        }
    else:
        context_text = get_context_text(text, st.session_state.transcript_window)
        text_vec     = vectorizer.transform([text])
        kw_score_ml, groups_hit_ml, _ = compute_keyword_score(text)
        TRAIN_GROUP_ORDER = [
        "authority","urgency","scarcity","warrant","money",
        "reciprocity","threat","account","distraction","social_proof","commitment"
        ]
        kw_flags = [
            (1 if any(kw in text.lower() for kw in CIALDINI_GROUPS[g]["keywords"]) else 0)
            if g in CIALDINI_GROUPS else 0
            for g in TRAIN_GROUP_ORDER
        ]
        
        num_vec  = csr_matrix([[kw_score_ml, len(groups_hit_ml),
                        1 if kw_score_ml > 0 else 0] + kw_flags])
        probability  = model.predict_proba(hstack([text_vec, num_vec]))[0][1]

        if probability < MIN_CONFIDENCE:
            new_score     = 0.0
            keyword_score = 0.0
            groups_hit    = set()
            combo_name    = None
        else:
            keyword_score, groups_hit, combo_name = compute_keyword_score(context_text)
            hits = len(groups_hit)
            if hits >= 2:
                st.session_state.keyword_hit_count += hits
                st.session_state.escalation_bonus   = min(st.session_state.escalation_bonus + 0.04 * hits, 0.35)
            else:
                st.session_state.escalation_bonus   = max(st.session_state.escalation_bonus - 0.02, 0.0)
            raw_score = min(probability + 0.10 * keyword_score + st.session_state.escalation_bonus, 1.0)
            prev      = st.session_state.current_score
            new_score = prev + (raw_score - prev) * (0.8 if raw_score > prev else 0.3)

        entry = {
            "speaker": "attacker", "time": now, "text": text,
            "score": new_score, "ml": probability if probability >= MIN_CONFIDENCE else 0.0,
            "keywords": keyword_score if probability >= MIN_CONFIDENCE else 0.0,
            "groups": list(groups_hit) if probability >= MIN_CONFIDENCE else [],
            "combo": combo_name if probability >= MIN_CONFIDENCE else None,
            "emotions": detect_emotions(text),
        }

    st.session_state.current_score        = entry["score"]
    st.session_state.total_chunks        += 1
    st.session_state.last_attacker_score  = entry["score"]
    st.session_state.last_attacker_groups = entry["groups"]
    if entry["score"] > 0.38:
        st.session_state.high_risk_count += 1
    st.session_state.history.append(entry)
    st.session_state.conversation.append({
        "speaker": "attacker", "text": text, "score": entry["score"],
        "groups": entry["groups"], "combo": entry["combo"], "time": now,
    })
    st.session_state.risk_timeline.append((now, entry["score"]))
    st.session_state.last_attacker_chunk = entry


def process_victim_chunk(text):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    compliance_score, response_type = score_victim_response(
        text, st.session_state.last_attacker_groups, st.session_state.last_attacker_score)
    if compliance_score > 0.15:
        st.session_state.consecutive_compliances += 1
    else:
        st.session_state.consecutive_compliances = 0
    entry = {
        "speaker": "victim", "time": now, "text": text,
        "score": 0.0, "ml": 0.0, "keywords": 0.0,
        "groups": [], "combo": None, "emotions": [],
        "compliance_score": compliance_score, "response_type": response_type,
    }
    st.session_state.history.append(entry)
    st.session_state.conversation.append({
        "speaker": "victim", "text": text, "score": 0.0,
        "groups": [], "combo": None,
        "compliance_score": compliance_score,
        "response_type": response_type, "time": now,
    })
    st.session_state.last_victim_chunk = entry


# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>🛡️ SCAM SHIELD</h1>
    <div class="subtitle">Real-Time Digital Arrest Scam Detection System</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# BUTTON HANDLERS — process first, render after.
# Streamlit reruns the entire script when a button is clicked.
# These run before any st.columns / st.markdown calls, so state
# is fully updated by the time the layout renders below.
# ══════════════════════════════════════════════════════════════
c1, c2, c3, c4 = st.columns(4)
reset_btn    = c1.button("🔄 NEW CALL",         type="primary", use_container_width=True)
attacker_btn = c2.button("🔴 RECORD ATTACKER",                  use_container_width=True)
victim_btn   = c3.button("🟢 RECORD VICTIM",                    use_container_width=True)
analyse_btn  = c4.button("🧠 CALCULATE RISK",                   use_container_width=True)

if reset_btn:
    for k, v in _fresh_state().items():
        st.session_state[k] = v

# elif attacker_btn:
#     with st.spinner("🎙️ Recording attacker... speak now"):
#         text = record_and_transcribe()
#     if not text:
#         st.warning("🔇 No speech detected. Try again.")
#     else:
#         process_attacker_chunk(text)
elif attacker_btn:
    with st.spinner("🎙️ Recording attacker... speak now"):
        try:
            text = record_and_transcribe()
        except Exception as e:
            import traceback
            with open("C:/digital_arrest_detector/debug_log.txt", "w") as f:
                f.write(traceback.format_exc())
            st.session_state.status_msg = f"❌ CRASH: {e}"
            text = None
    if text is None:
        with open("C:/digital_arrest_detector/debug_log.txt", "a") as f:
            f.write(f"text was None after record_and_transcribe\n")
    else:
        with open("C:/digital_arrest_detector/debug_log.txt", "w") as f:
            f.write(f"SUCCESS: text='{text}' conv_len={len(st.session_state.conversation)}\n")
        process_attacker_chunk(text)
    
    if not text:
        st.session_state.status_msg = st.session_state.status_msg or "❌ record_and_transcribe returned None"
    # else:
    #     st.session_state.status_msg = f"✅ Got text: '{text}' — calling process_attacker_chunk"
    #     process_attacker_chunk(text)
    #     st.session_state.status_msg += f" | conversation length now: {len(st.session_state.conversation)}"
    else:
        st.session_state.status_msg = f"✅ Got text: '{text}' — calling process_attacker_chunk"
        process_attacker_chunk(text)
        st.session_state.status_msg += f" | conversation length now: {len(st.session_state.conversation)}"
        with open("C:/digital_arrest_detector/debug_log.txt", "a") as f:
            f.write(f"{datetime.datetime.now()} | text='{text}' | conv_len={len(st.session_state.conversation)}\n")

elif victim_btn:
    with st.spinner("🎙️ Recording victim... speak now"):
        text = record_and_transcribe()
    if not text:
        st.warning("🔇 No speech detected. Try again.")
    else:
        process_victim_chunk(text)

elif analyse_btn:
    attacker_turns_btn = [t for t in st.session_state.conversation if t["speaker"] == "attacker"]
    # DEBUG — remove after confirming recordings work
    st.info(f"DEBUG: conversation has {len(st.session_state.conversation)} entries, {len(attacker_turns_btn)} attacker turns")
    if not attacker_turns_btn:
        st.warning("Record at least one attacker turn first.")
    else:
        from collections import Counter
        _err = None
        try:
            predictor = ConversationPredictor()
            r = predictor.predict(st.session_state.conversation)
            if r is not None:
                st.session_state.final_result        = r
                st.session_state.final_analysis_done = True
                _err = None
            else:
                _err = "ML predictor returned None"
        except Exception as e:
            _err = str(e)

        if _err is not None:
            # ML failed — run rule-based fallback directly
            r = analyse_full_conversation(st.session_state.conversation)
            if r is None:
                # Attacker-only fallback — no victim turns needed
                scores  = [t["score"] for t in attacker_turns_btn]
                avg_s   = sum(scores) / len(scores)
                peak_s  = max(scores)
                final_s = round(min(avg_s * 0.6 + peak_s * 0.4, 1.0), 3)
                if   final_s > 0.65: verdict, rcolor = "HIGH FRAUD RISK",         "#cc0000"
                elif final_s > 0.40: verdict, rcolor = "SUSPICIOUS CONVERSATION",  "#ff8800"
                elif final_s > 0.20: verdict, rcolor = "LOW RISK — Monitor",       "#ffcc00"
                else:                verdict, rcolor = "SAFE CONVERSATION",         "#00cc55"
                all_groups = []
                for t in attacker_turns_btn:
                    all_groups.extend(t.get("groups", []))
                r = {
                    "final_score":          final_s,
                    "verdict":              verdict,
                    "color":                rcolor,
                    "avg_attacker":         round(avg_s, 3),
                    "peak_attacker":        round(peak_s, 3),
                    "avg_compliance":       0.0,
                    "info_disclosed":       False,
                    "dominant_principles":  [g for g, _ in Counter(all_groups).most_common(3)],
                    "resistance_count":     0,
                    "num_principles":       len(set(all_groups)),
                    "attacker_turns":       len(attacker_turns_btn),
                    "victim_turns":         0,
                }
            r["_fallback"]               = True
            r["_fallback_reason"]        = _err
            st.session_state.final_result        = r
            st.session_state.final_analysis_done = True


st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# MAIN LAYOUT  — 3 columns: left (attacker), centre (victim), right (log)
# Gauge + metrics live above all three in a shared strip.
# ══════════════════════════════════════════════════════════════

# ── Top metrics strip ─────────────────────────────────────────
sp = int(st.session_state.current_score * 100)
sc = "red" if sp > 38 else ("orange" if sp > 22 else "green")
rc = "red" if st.session_state.high_risk_count > 0 else "green"
eb = int(st.session_state.escalation_bonus * 100)
ec = "red" if eb > 20 else ("orange" if eb > 10 else "green")
def _box(label, val, cls=""):
    return (f'<div class="metric-box"><div class="metric-label">{label}</div>'
            f'<div class="metric-value {cls}">{val}</div></div>')
if st.session_state.status_msg:
    st.info(st.session_state.status_msg)
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(_box("TURNS",      st.session_state.total_chunks,    ""),  unsafe_allow_html=True)
m2.markdown(_box("HIGH RISK",  st.session_state.high_risk_count, rc),  unsafe_allow_html=True)
m3.markdown(_box("LIVE RISK",  f"{sp}%",                         sc),  unsafe_allow_html=True)
m4.markdown(_box("ESCALATION", f"+{eb}%",                        ec),  unsafe_allow_html=True)
m5.markdown(_box("COMPLIANCE", f"{round(st.session_state.last_attacker_score,2)}", sc), unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ── Gauge (full width, always visible) ───────────────────────
gauge_score = st.session_state.current_score
gval = gauge_score * 100
if gval > 38:
    gc, gn = "#cc0000", "#ff2200"
    gsteps = [('#001a06',0,22),('#1a0c00',22,38),('#2a0000',38,100)]
elif gval > 22:
    gc, gn = "#cc6600", "#ff8800"
    gsteps = [('#001a06',0,22),('#1a0c00',22,38),('#1a0000',38,100)]
else:
    gc, gn = "#00aa44", "#00cc55"
    gsteps = [('#001a06',0,22),('#0a1a00',22,38),('#180000',38,100)]

gauge_fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=gval,
    number={'suffix':"%", 'font':{'color':gc,'size':28,'family':'Share Tech Mono'}},
    title={'text':"LIVE FRAUD RISK",'font':{'color':'#2a3044','size':10,'family':'Share Tech Mono'}},
    gauge={
        'axis':{'range':[0,100],'tickcolor':'#131827','tickfont':{'color':'#2a3044','size':8},'tickwidth':1},
        'bar':{'color':gc,'thickness':0.2},
        'bgcolor':'#0b0e1a','borderwidth':0,
        'steps':[{'range':[s[1],s[2]],'color':s[0]} for s in gsteps],
        'threshold':{'line':{'color':gn,'width':3},'thickness':0.8,'value':gval}
    }
))
gauge_fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font={'color':'#d0d8f0'}, height=200,
    margin=dict(t=30, b=4, l=20, r=20)
)
st.plotly_chart(gauge_fig, use_container_width=True, key=f"gauge_{st.session_state.total_chunks}")

# ── Three-column live panels ──────────────────────────────────
atk_col, vic_col, log_col = st.columns([5, 5, 4], gap="medium")


# ════════════════════════════════════════════════════════════════
# LEFT — ATTACKER PANEL
# last_attacker_chunk is ONLY written by process_attacker_chunk.
# Recording victim NEVER touches this. Persists across all reruns.
# ════════════════════════════════════════════════════════════════
with atk_col:
    st.markdown('<div class="section-title">🔴 &nbsp; ATTACKER</div>', unsafe_allow_html=True)
    la = st.session_state.last_attacker_chunk

    if la is None:
        st.markdown(
            '<div style="background:#0b0e1a;border:1px solid #1a0010;border-radius:8px;'
            'padding:20px;text-align:center;color:#331122;font-family:Share Tech Mono,'
            'monospace;font-size:0.65rem;letter-spacing:2px;min-height:80px;">'
            'AWAITING ATTACKER SPEECH</div>', unsafe_allow_html=True)
    else:
        asc = la["score"]
        if asc > 0.38:
            ab, ac, al = "#cc0000","#ff2200","⚠ HIGH FRAUD RISK"
        elif asc > 0.22:
            ab, ac, al = "#cc5500","#ff8800","⚡ SUSPICIOUS"
        else:
            ab, ac, al = "#004422","#00cc55","✓ LOW RISK"

        st.markdown(
            f'<div style="border:1px solid {ab};border-radius:6px;padding:6px 10px;'
            f'text-align:center;font-family:Share Tech Mono,monospace;font-size:0.85rem;'
            f'color:{ac};letter-spacing:2px;margin-bottom:6px;">'
            f'{al} — {int(asc*100)}%</div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="transcript-box">{la["text"]}</div>', unsafe_allow_html=True)

        if la.get("emotions"):
            badges = "".join(f'<span class="emotion-badge {ecls}">{eico} {emo}</span>'
                             for emo, ecls, eico in la["emotions"])
            st.markdown(f'<div style="margin:5px 0;">{badges}</div>', unsafe_allow_html=True)

        groups_str = ", ".join(sorted(la.get("groups", []))) or "none"
        combo_str  = f' &nbsp;⚡ {la["combo"]}' if la.get("combo") else ""
        st.markdown(
            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.58rem;'
            f'color:#2a3044;margin-top:5px;line-height:1.8;">'
            f'GROUPS: <span style="color:#aa2244">{groups_str}</span>{combo_str}<br>'
            f'ML={round(la["ml"],2)} &nbsp; KW={round(la["keywords"],2)} &nbsp;'
            f'ESC=+{round(st.session_state.escalation_bonus,2)}'
            f'</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# CENTRE — VICTIM PANEL
# last_victim_chunk is ONLY written by process_victim_chunk.
# Recording attacker NEVER touches this.
# ════════════════════════════════════════════════════════════════
with vic_col:
    st.markdown('<div class="section-title">🟢 &nbsp; VICTIM</div>', unsafe_allow_html=True)
    lv = st.session_state.last_victim_chunk

    if lv is None:
        st.markdown(
            '<div style="background:#0b0e1a;border:1px solid #001a08;border-radius:8px;'
            'padding:20px;text-align:center;color:#112211;font-family:Share Tech Mono,'
            'monospace;font-size:0.65rem;letter-spacing:2px;min-height:80px;">'
            'AWAITING VICTIM RESPONSE</div>', unsafe_allow_html=True)
    else:
        cs  = lv.get("compliance_score", 0.0)
        rt  = lv.get("response_type", "neutral")
        bar = min(int(abs(cs) * 100), 100)

        if rt == "resistance":
            vb, vc, vl = "#00aa44","#00cc55","✋ RESISTANT"
        elif rt == "info_leak":
            vb, vc, vl = "#cc0000","#ff2200","🚨 INFO LEAKED"
        elif cs > 0.3:
            vb, vc, vl = "#cc0000","#ff4444","⚠ HIGH COMPLIANCE"
        elif cs > 0.1:
            vb, vc, vl = "#cc5500","#ff8800","⚡ PARTIAL COMPLIANCE"
        else:
            vb, vc, vl = "#004422","#00cc55","✓ NEUTRAL"

        st.markdown(
            f'<div style="border:1px solid {vb};border-radius:6px;padding:6px 10px;'
            f'text-align:center;font-family:Share Tech Mono,monospace;font-size:0.85rem;'
            f'color:{vc};letter-spacing:2px;margin-bottom:6px;">'
            f'{vl}</div>', unsafe_allow_html=True)

        # Compliance bar
        st.markdown(
            f'<div style="margin-bottom:6px;">'
            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.55rem;'
            f'color:#2a3044;letter-spacing:2px;margin-bottom:3px;">COMPLIANCE SCORE: {round(cs,2)}</div>'
            f'<div style="background:#0b0e1a;border:1px solid #131827;border-radius:3px;height:8px;">'
            f'<div style="width:{bar}%;height:100%;background:{vc};border-radius:3px;"></div>'
            f'</div></div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="transcript-box">{lv["text"]}</div>', unsafe_allow_html=True)

        st.markdown(
            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.58rem;'
            f'color:#2a3044;margin-top:5px;line-height:1.8;">'
            f'TYPE: <span style="color:#1e6fff">{rt}</span> &nbsp;'
            f'STREAK: <span style="color:#ff8800">{st.session_state.consecutive_compliances}</span>'
            f'</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# RIGHT — CALL LOG + TIMELINE
# ════════════════════════════════════════════════════════════════
with log_col:
    st.markdown('<div class="section-title">📋 &nbsp; CALL LOG</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown(
            '<div style="color:#1a2030;font-family:Share Tech Mono,monospace;'
            'font-size:0.65rem;letter-spacing:2px;text-align:center;padding:16px 0;">'
            'NO ENTRIES YET</div>', unsafe_allow_html=True)
    else:
        html = ""
        for e in reversed(st.session_state.history[-15:]):
            speaker = e.get("speaker", "attacker")
            sp2     = int(e["score"] * 100)
            if speaker == "victim":
                cs2, rt2 = e.get("compliance_score", 0.0), e.get("response_type", "neutral")
                if rt2 == "resistance":
                    tc, badge = "safe-tag",   "✋ RESISTANT"
                elif rt2 == "info_leak":
                    tc, badge = "danger-tag", "🚨 INFO LEAKED"
                elif cs2 > 0.3:
                    tc, badge = "danger-tag", f"⚠ COMPLY {round(cs2,2)}"
                elif cs2 > 0.1:
                    tc, badge = "warn-tag",   f"⚡ {round(cs2,2)}"
                else:
                    tc, badge = "safe-tag",   "✓ NEUTRAL"
                slabel = '<span style="color:#00cc55;font-size:0.55rem;">🟢 VICTIM</span>'
            else:
                tc, badge = (("danger-tag", f"⚠ {sp2}%") if e["score"] > 0.38
                             else ("warn-tag", f"⚡ {sp2}%") if e["score"] > 0.22
                             else ("safe-tag",  f"✓ {sp2}%"))
                slabel = '<span style="color:#cc0000;font-size:0.55rem;">🔴 ATTACKER</span>'
            safe_text = str(e.get("text",""))[:80] + ("…" if len(str(e.get("text",""))) > 80 else "")
            html += (
                '<div class="history-entry">'
                f'<div class="history-time">{e["time"]} &nbsp; {slabel}</div>'
                f'<div class="history-text">{safe_text}</div>'
                f'<div class="{tc}">{badge}</div>'
                '</div>'
            )
        st.markdown(html, unsafe_allow_html=True)

    # Risk timeline
    st.markdown('<div class="section-title" style="margin-top:10px;">📈 TIMELINE</div>',
                unsafe_allow_html=True)
    tl = st.session_state.risk_timeline
    if len(tl) >= 2:
        times  = [t[0] for t in tl]
        scores = [t[1]*100 for t in tl]
        colors = ["#cc0000" if s>38 else "#ff8800" if s>22 else "#00cc55" for s in scores]
        tfig = go.Figure()
        tfig.add_hrect(y0=0,  y1=22,  fillcolor="rgba(0,204,85,0.05)",  line_width=0)
        tfig.add_hrect(y0=22, y1=38,  fillcolor="rgba(255,136,0,0.05)", line_width=0)
        tfig.add_hrect(y0=38, y1=100, fillcolor="rgba(204,0,0,0.06)",   line_width=0)
        tfig.add_trace(go.Scatter(x=times, y=scores, mode='lines+markers',
            line=dict(color='#1e6fff', width=2),
            marker=dict(color=colors, size=6),
            fill='tozeroy', fillcolor='rgba(30,111,255,0.06)'))
        tfig.add_hline(y=22, line=dict(color="rgba(255,136,0,0.4)", width=1, dash="dot"))
        tfig.add_hline(y=38, line=dict(color="rgba(204,0,0,0.4)",   width=1, dash="dot"))
        tfig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=130, margin=dict(t=4,b=20,l=26,r=4),
            xaxis=dict(showgrid=False, tickfont=dict(color='#2a3044',size=7), tickangle=-30, color='#2a3044'),
            yaxis=dict(showgrid=False, range=[0,100], tickfont=dict(color='#2a3044',size=7),
                       tickvals=[0,22,38,100], color='#2a3044'),
            showlegend=False)
        st.plotly_chart(tfig, use_container_width=True, key=f"tl_{len(tl)}")
    else:
        st.markdown(
            '<div style="color:#2a3044;font-family:Share Tech Mono,monospace;'
            'font-size:0.62rem;text-align:center;padding:8px 0;">AWAITING DATA...</div>',
            unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# FINAL ANALYSIS PANEL — shown below all columns
# ══════════════════════════════════════════════════════════════
if st.session_state.final_analysis_done and st.session_state.final_result:
    r           = st.session_state.final_result
    is_ml       = "combined_score" in r
    is_fallback = r.get("_fallback", False)
    score       = r.get("combined_score", r.get("final_score", 0.0))
    color       = r["color"]

    st.markdown("---")

    layer_blocks = ""
    if is_ml and not is_fallback:
        layer_blocks = (
            f'<div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;margin-bottom:12px;">'
            f'<div style="background:#06080f;border:1px solid #1a2030;border-radius:6px;padding:8px 14px;min-width:110px;text-align:center;">'
            f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;margin-bottom:3px;">LAYER 1 — SENTENCE ML</div>'
            f'<div style="font-size:1.1rem;color:#1e6fff;">{int(r["ml1_avg_score"]*100)}%</div></div>'
            f'<div style="background:#06080f;border:1px solid #1a2030;border-radius:6px;padding:8px 14px;min-width:110px;text-align:center;">'
            f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;margin-bottom:3px;">LAYER 2 — CONVERSATION ML</div>'
            f'<div style="font-size:1.1rem;color:#cc0000;">{int(r["ml2_score"]*100)}%</div></div>'
            f'<div style="background:#06080f;border:1px solid {color};border-radius:6px;padding:8px 14px;min-width:110px;text-align:center;">'
            f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;margin-bottom:3px;">ENSEMBLE FINAL</div>'
            f'<div style="font-size:1.1rem;color:{color};">{int(score*100)}%</div></div>'
            f'</div>'
        )

    info_block = (
        '<div style="color:#cc0000;font-size:0.8rem;font-weight:bold;border:1px solid #cc0000;'
        'border-radius:4px;padding:6px;margin-top:6px;">🚨 CRITICAL: PERSONAL INFORMATION WAS DISCLOSED</div>'
    ) if r.get("info_disclosed") else ""

    bd       = r.get("breakdown", {})
    comp_val = round(r.get("avg_compliance", bd.get("compliance_avg", 0.0)), 2)
    res_val  = r.get("resistance_count", 0)
    pri_val  = r.get("num_principles", 0)
    dom_str  = ", ".join(r.get("dominant_principles", [])) or "none"
    atk_t    = r.get("attacker_turns", bd.get("attacker_turns", "?"))
    vic_t    = r.get("victim_turns",   bd.get("victim_turns",   "?"))
    fallback_reason = r.get("_fallback_reason", "")
    title_text = ("DUAL-LAYER ML ANALYSIS" if (is_ml and not is_fallback)
                  else f"RULE-BASED ANALYSIS" + (f" — ML: {fallback_reason[:60]}" if fallback_reason else ""))

    st.markdown(
        f'<div style="font-family:Share Tech Mono,monospace;text-align:center;padding:22px;'
        f'background:#0b0e1a;border:2px solid {color};border-radius:10px;">'
        f'<div style="font-size:0.6rem;color:#2a3044;letter-spacing:3px;margin-bottom:8px;">{title_text}</div>'
        f'<div style="font-size:2.4rem;color:{color};text-shadow:0 0 24px {color}55;font-weight:bold;">{int(score*100)}%</div>'
        f'<div style="font-size:0.95rem;color:{color};letter-spacing:2px;margin:4px 0 14px 0;">{r["verdict"]}</div>'
        f'{layer_blocks}'
        f'<div style="display:flex;justify-content:center;gap:20px;flex-wrap:wrap;font-size:0.6rem;color:#2a3044;margin-bottom:8px;">'
        f'<span>AVG COMPLIANCE: <span style="color:#ff8800">{comp_val}</span></span>'
        f'<span>RESISTANCE: <span style="color:#00cc55">{res_val}</span></span>'
        f'<span>PRINCIPLES HIT: <span style="color:#1e6fff">{pri_val}</span></span>'
        f'<span>ATTACKER TURNS: <span style="color:#cc0000">{atk_t}</span></span>'
        f'<span>VICTIM TURNS: <span style="color:#00cc55">{vic_t}</span></span>'
        f'</div>'
        f'<div style="font-size:0.6rem;color:#2a3044;">DOMINANT PRINCIPLES: <span style="color:#1e6fff">{dom_str}</span></div>'
        f'{info_block}</div>',
        unsafe_allow_html=True)

    # Full conversation transcript
    st.markdown(
        '<div class="section-title" style="margin-top:16px;margin-bottom:6px;">📜 FULL CONVERSATION</div>',
        unsafe_allow_html=True)
    conv_html = ""
    for turn in st.session_state.conversation:
        spk   = turn["speaker"]
        lclr  = "#cc0000" if spk == "attacker" else "#00cc55"
        label = "🔴 ATTACKER" if spk == "attacker" else "🟢 VICTIM"
        score_str = (f' <span style="color:{lclr};font-size:0.58rem;">[{int(turn["score"]*100)}%]</span>'
                     if spk == "attacker" and turn["score"] > 0 else "")
        conv_html += (
            f'<div style="background:#080c15;border:1px solid #0f1525;border-radius:5px;'
            f'padding:7px 10px;margin-bottom:5px;">'
            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.56rem;color:{lclr};margin-bottom:3px;">'
            f'{turn["time"]} &nbsp; {label}{score_str}</div>'
            f'<div style="color:#7788aa;font-size:0.78rem;line-height:1.4;">{turn["text"]}</div>'
            f'</div>'
        )
    st.markdown(conv_html or
        '<div style="color:#2a3044;font-family:Share Tech Mono,monospace;font-size:0.65rem;'
        'text-align:center;padding:10px 0;">NO CONVERSATION DATA</div>',
        unsafe_allow_html=True)