# import streamlit as st
# from faster_whisper import WhisperModel
# import joblib
# import sounddevice as sd
# import numpy as np
# from scipy.io.wavfile import write
# import plotly.graph_objects as go
# import plotly.express as px
# import time
# import datetime
# from scipy.sparse import hstack, csr_matrix

# # Import conversation-level predictor (Layer 2)
# import sys, os
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# try:
#     from predict_conversation import ConversationPredictor
#     CONV_MODEL_AVAILABLE = True
# except Exception:
#     CONV_MODEL_AVAILABLE = False

# # ---------------------------
# # Page Config
# # ---------------------------
# st.set_page_config(
#     page_title="Scam Shield",
#     page_icon="🛡️",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# # ---------------------------
# # CSS
# # ---------------------------
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

# html, body, [class*="css"] {
#     background-color: #06080f !important;
#     color: #d0d8f0;
#     font-family: 'Rajdhani', sans-serif;
# }
# .stApp {
#     background: #06080f;
#     background-image:
#         radial-gradient(ellipse at 10% 10%, #1a000822 0%, transparent 50%),
#         radial-gradient(ellipse at 90% 90%, #00102a22 0%, transparent 50%);
# }
# #MainMenu, footer, header { visibility: hidden; }

# .main-header {
#     text-align: center;
#     padding: 10px 0 7px 0;
#     border-bottom: 1px solid #cc000033;
#     margin-bottom: 12px;
# }
# .main-header h1 {
#     font-family: 'Share Tech Mono', monospace;
#     font-size: 1.65rem;
#     color: #cc0000;
#     letter-spacing: 6px;
#     text-shadow: 0 0 22px #cc000055;
#     margin: 0;
# }
# .main-header .subtitle {
#     color: #1e6fff;
#     font-size: 0.65rem;
#     letter-spacing: 4px;
#     margin: 3px 0 0 0;
#     text-transform: uppercase;
#     opacity: 0.8;
# }

# .mic-wrapper {
#     display: flex; flex-direction: column;
#     align-items: center; margin: 3px 0 4px 0;
# }
# .mic-btn {
#     width: 58px; height: 58px; border-radius: 50%;
#     background: radial-gradient(circle at 35% 35%, #120010, #06080f);
#     border: 2px solid #441133;
#     display: flex; align-items: center; justify-content: center;
#     font-size: 1.5rem;
#     box-shadow: 0 0 12px #33004422, inset 0 0 10px #00000088;
#     cursor: default; transition: all 0.3s ease;
# }
# .mic-btn.active {
#     border-color: #cc0000;
#     box-shadow: 0 0 0 5px #cc000022, 0 0 0 11px #cc000011,
#                 0 0 26px #ff220055, inset 0 0 12px #00000088;
#     animation: mic-pulse 1.2s ease-in-out infinite;
# }
# @keyframes mic-pulse {
#     0%,100% { box-shadow: 0 0 0 5px #cc000033, 0 0 0 12px #cc000011, 0 0 26px #ff220044; }
#     50%      { box-shadow: 0 0 0 9px #cc000055, 0 0 0 18px #cc000022, 0 0 42px #ff220088; }
# }
# .mic-label {
#     font-family: 'Share Tech Mono', monospace;
#     font-size: 0.58rem; letter-spacing: 3px; color: #334455;
#     margin-top: 4px; text-transform: uppercase;
# }
# .mic-label.active { color: #ff2200; }

# .soundwave {
#     display: flex; align-items: center; gap: 3px;
#     height: 26px; justify-content: center; margin: 2px auto 4px auto;
# }
# .soundwave .bar {
#     width: 3px; border-radius: 2px;
#     background: linear-gradient(to top, #cc0000, #1e6fff);
#     animation: wave 0.9s ease-in-out infinite;
# }
# .soundwave .bar:nth-child(1){animation-delay:0.00s;height:6px}
# .soundwave .bar:nth-child(2){animation-delay:0.10s;height:13px}
# .soundwave .bar:nth-child(3){animation-delay:0.20s;height:20px}
# .soundwave .bar:nth-child(4){animation-delay:0.30s;height:26px}
# .soundwave .bar:nth-child(5){animation-delay:0.40s;height:17px}
# .soundwave .bar:nth-child(6){animation-delay:0.30s;height:26px}
# .soundwave .bar:nth-child(7){animation-delay:0.20s;height:20px}
# .soundwave .bar:nth-child(8){animation-delay:0.10s;height:13px}
# .soundwave .bar:nth-child(9){animation-delay:0.00s;height:6px}
# @keyframes wave {
#     0%,100%{transform:scaleY(0.25);opacity:0.4}
#     50%{transform:scaleY(1);opacity:1}
# }
# .soundwave.idle .bar { height:4px !important; animation:none; opacity:0.15; }

# div[data-testid="column"] .stButton > button {
#     width: 100%; font-family: 'Share Tech Mono', monospace;
#     letter-spacing: 2px; font-size: 0.8rem;
#     height: 36px; border-radius: 6px; border: none;
#     transition: all 0.2s ease;
# }

# .status-safe {
#     background:#00100a; border:1px solid #00aa44; color:#00cc55;
#     padding:6px 12px; border-radius:6px;
#     font-family:'Share Tech Mono',monospace; font-size:0.85rem;
#     text-align:center; letter-spacing:3px; text-shadow:0 0 8px #00cc5544;
# }
# .status-listening {
#     background:#0a0014; border:1px solid #5533aa; color:#8866ee;
#     padding:6px 12px; border-radius:6px;
#     font-family:'Share Tech Mono',monospace; font-size:0.85rem;
#     text-align:center; letter-spacing:3px;
# }
# .status-warning {
#     background:#150800; border:1px solid #cc5500; color:#ff8800;
#     padding:6px 12px; border-radius:6px;
#     font-family:'Share Tech Mono',monospace; font-size:0.85rem;
#     text-align:center; letter-spacing:3px; text-shadow:0 0 8px #cc550044;
# }
# .status-danger {
#     background:#190000; border:1px solid #cc0000; color:#ff2200;
#     padding:6px 12px; border-radius:6px;
#     font-family:'Share Tech Mono',monospace; font-size:0.85rem;
#     text-align:center; letter-spacing:3px;
#     animation:pulse 1s infinite; text-shadow:0 0 10px #cc000066;
# }
# @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.55} }

# .emotion-badge {
#     display:inline-block; padding:3px 10px; border-radius:12px;
#     font-family:'Share Tech Mono',monospace; font-size:0.72rem;
#     letter-spacing:2px; margin:3px 3px 0 0;
# }
# .emo-fear    { background:#1a0022; border:1px solid #aa00ff; color:#cc66ff; }
# .emo-anger   { background:#1a0000; border:1px solid #cc0000; color:#ff4444; }
# .emo-urgency { background:#150800; border:1px solid #cc5500; color:#ff8800; }
# .emo-coerce  { background:#001020; border:1px solid #0066aa; color:#3399ff; }
# .emo-calm    { background:#001a08; border:1px solid #00aa44; color:#33cc66; }

# .metric-box {
#     background:#0b0e1a; border:1px solid #131827;
#     border-radius:7px; padding:6px 4px; text-align:center;
# }
# .metric-label { font-size:0.55rem; color:#2a3044; letter-spacing:2px; text-transform:uppercase; margin-bottom:2px; }
# .metric-value { font-family:'Share Tech Mono',monospace; font-size:1.15rem; color:#1e6fff; }
# .metric-value.red   { color:#cc0000; }
# .metric-value.green { color:#00cc55; }
# .metric-value.orange{ color:#ff8800; }

# .transcript-box {
#     background:#080c15; border:1px solid #131827; border-radius:6px;
#     padding:7px 11px; font-family:'Share Tech Mono',monospace;
#     font-size:0.76rem; color:#7788aa;
#     min-height:40px; max-height:68px; overflow-y:auto;
#     line-height:1.5; word-break:break-word;
# }
# .section-title {
#     font-family:'Share Tech Mono',monospace; font-size:0.58rem;
#     color:#2a3044; letter-spacing:3px; text-transform:uppercase; margin-bottom:4px;
# }

# .history-entry {
#     background:#080c15; border:1px solid #0f1525;
#     border-radius:5px; padding:6px 9px; margin-bottom:4px;
# }
# .history-time { font-family:'Share Tech Mono',monospace; font-size:0.58rem; color:#2a3044; margin-bottom:2px; }
# .history-text { color:#7788aa; font-size:0.76rem; margin-bottom:2px; line-height:1.35; }
# .safe-tag    { color:#00cc55; font-family:'Share Tech Mono',monospace; font-size:0.68rem; font-weight:bold; }
# .warn-tag    { color:#ff8800; font-family:'Share Tech Mono',monospace; font-size:0.68rem; font-weight:bold; }
# .danger-tag  { color:#cc0000; font-family:'Share Tech Mono',monospace; font-size:0.68rem; font-weight:bold; }

# ::-webkit-scrollbar { width:3px; }
# ::-webkit-scrollbar-track { background:#080c15; }
# ::-webkit-scrollbar-thumb { background:#cc0000; border-radius:2px; }
# .js-plotly-plot { background:transparent !important; }
# </style>
# """, unsafe_allow_html=True)

# # ---------------------------
# # Load Models
# # ---------------------------
# @st.cache_resource(show_spinner=False)
# def load_models():
#     wm = WhisperModel(
#     "base",
#     device="cpu",
#     compute_type="int8"
# )
#     m  = joblib.load("models/scam_model.pkl")
#     v  = joblib.load("models/vectorizer.pkl")
#     return wm, m, v

# whisper_model, model, vectorizer = load_models()


# # ---------------------------
# # Cialdini Keyword Groups
# # ---------------------------
# CIALDINI_GROUPS = {
#     "authority": {
#         "score": 0.30,
#         "keywords": [
#             "cbi officer","cyber crime department","enforcement directorate",
#             "income tax officer","trai officer","rbi officer","narcotics",
#             "anti terrorism squad","national investigation agency",
#             "financial intelligence unit","economic offences wing",
#             "serious fraud investigation office","sebi officer",
#             "ministry of home affairs","supreme court","high court",
#             "sessions court","magistrate","central vigilance commission",
#             "inspector general","deputy commissioner","superintendent of police",
#             "cid officer","joint director","directorate of revenue intelligence",
#             "sfio","lokayukta","lokpal","cert-in","intelligence bureau",
#             "national crime records bureau","interpol","ed officer",
#             "anti corruption bureau","election commission","dcp",
#             "nia officer","crime branch","vigilance officer","police officer",
#             "government officer","court appointed","judicial officer",
#             "senior officer","investigation officer","cyber cell",
#             "national cyber crime","treasury officer",
#             "jaanch adhikaari","sarkaari adhikaari","vibhaag se",
#             "cbi se hain","police vibhaag","court ka order",
#         ]
#     },
#     "urgency": {
#         "score": 0.30,
#         "keywords": [
#             "within 24 hours","immediately","right now","last chance",
#             "final notice","last warning","within 2 hours","60 minutes",
#             "30 minutes","45 minutes","tonight","today only",
#             "no time left","before midnight","by end of day",
#             "abhi","turant","abhi ke abhi","24 ghante mein",
#             "ek ghante mein","2 ghante mein","aaj raat tak",
#             "aaj tak","jaldi karo","der mat karo","aakhri mauka",
#             "last date","deadline","act now","do not delay",
#             "final opportunity","last moment","running out of time",
#         ]
#     },
#     "scarcity": {
#         "score": 0.25,
#         "keywords": [
#             "one time settlement","one time waiver","limited time offer",
#             "only chance","cannot be extended","no second chance",
#             "this offer expires","rare opportunity","special window",
#             "last opportunity","after this call","ek baar ka mauka",
#             "yeh mauka nahi milega","aakhri baar","ab nahi hoga",
#             "sirf aaj","only today","out of court settle",
#             "settlement window","after today no help",
#             "cannot help after this","government scheme aaj tak",
#         ]
#     },
#     "warrant": {
#         "score": 0.25,
#         "keywords": [
#             "arrest warrant","non-bailable warrant","look-out notice",
#             "court order","fir registered","fir darj","legal notice",
#             "summons","court summons","attachment order","seizure order",
#             "warrant execute","warrant issued","bailable warrant",
#             "anticipatory bail","preventive detention","section 420",
#             "pmla","fema violation","ipc section","contempt of court",
#             "sub judice","ex-parte order","charge sheet","bail rejected",
#             "giraftaari ka warrant","court notice","girtaari ka aadesh",
#             "non bailable","warrant aayega","notice aayega",
#         ]
#     },
#     "money": {
#         "score": 0.30,
#         "keywords": [
#             "transfer money","send money","pay immediately","transfer funds",
#             "wire transfer","pay fine","security deposit","processing fee",
#             "verification fee","settlement amount","clearance fee",
#             "pay the penalty","pay or face","deposit amount",
#             "escrow account","secret account","government account",
#             "paise transfer karo","abhi paise bhejo","turant transfer",
#             "fine bharo","fees bharo","payment karo","jama karo",
#             "amount bhejo","rupees transfer","lakh transfer",
#             "hawala payment","cash deposit","online payment karo",
#             "neft karo","rtgs karo","upi se bhejo",
#         ]
#     },
#     "reciprocity": {
#         "score": 0.20,
#         "keywords": [
#             "we are trying to help you","we want to protect you",
#             "i am on your side","we are your well-wishers",
#             "helping you out","doing you a favour","personally ensuring",
#             "i will personally","guarantee your safety","protect your family",
#             "immunity from prosecution","clean chit guarantee",
#             "case close karenge","aapko bachayenge","aapki help kar rahe hain",
#             "aapke saath hain","aapka bhala chahte hain",
#             "personally handle karunga","sifarish karenge",
#             "leniency dilaayenge","aapko protect karenge",
#             "hum guarantee dete hain","aapke liye kuch kar sakte hain",
#         ]
#     },
#     "threat": {
#         "score": 0.30,
#         "keywords": [
#             "face arrest","you will be arrested","arrested tonight",
#             "jail bheja jayega","prison mein jaoge","aapko pakad lenge",
#             "raid padegi","police aayegi","officer aa raha hai",
#             "property seized","assets frozen","account blocked",
#             "media mein aayega","employer ko batayenge","family ko involve",
#             "aapki beti arrested","aapka beta case mein","family member named",
#             "reputation destroy","public embarrassment","nationwide notice",
#             "travel ban","passport blacklisted","criminal record",
#             "dhamki","khatre mein","consequences severe",
#             "will not be able to help","cannot save you after this",
#         ]
#     },
#     "account": {
#         "score": 0.20,
#         "keywords": [
#             "share your otp","otp batao","account number share",
#             "net banking credentials","atm card number","cvv number",
#             "pin number","share bank details","verify account",
#             "aadhaar number share","pan number verify","account verification",
#             "kyc update","kyc verify karo","biometric verify",
#             "screen share karo","remote access","aadhar otp share",
#             "netbanking username","password share","login details",
#             "account details share","banking details","debit card details",
#             "credit card number","ifsc share","account froze",
#             "account suspend","aapka account block","frozen account",
#         ]
#     },
#     "distraction": {
#         "score": 0.25,
#         "keywords": [
#             "sealed case","confidential investigation","classified matter",
#             "national security","media blackout","nda sign karo",
#             "do not tell anyone","kisi ko mat batao","keep this confidential",
#             "do not contact lawyer","do not inform family",
#             "this is a secret operation","sub judice matter",
#             "sensitive case","high profile matter","sealed envelope",
#             "stay on the line","do not hang up","do not disconnect",
#             "aap monitored hain","call record ho rahi hai",
#             "yeh recorded call hai","evidence ke roop mein",
#         ]
#     },
#     "social_proof": {
#         "score": 0.20,
#         "keywords": [
#             "multiple complaints against you","47 complaints",
#             "23 complaints","witnesses against you","3 witnesses",
#             "your neighbor reported","your employee reported",
#             "your business partner named you","your friend is a witness",
#             "your family member named","anonymous complaint",
#             "whistleblower aayi hai","gawah hain aapke khilaf",
#             "3 independent witnesses","complaints received",
#             "national portal par complaints","public complaints",
#         ]
#     },
#     "commitment": {
#         "score": 0.20,
#         "keywords": [
#             "you already agreed","you said you would cooperate",
#             "stay on call","remain on line","do not move from location",
#             "you have acknowledged","legal obligation","legally bound",
#             "mandatory compliance","you must cooperate",
#             "aap agree kar chuke hain","aapko cooperate karna hoga",
#             "aap legally bound hain","aapko comply karna hoga",
#             "aap pe legal obligation hai","undertaking sign karni hogi",
#             "affidavit deni hogi","you are obligated","cooperation mandatory",
#         ]
#     },
# }

# COMBINATIONS = [
#     {"groups":["commitment","reciprocity","distraction"], "bonus":0.35},
#     {"groups":["authority","urgency","threat"],           "bonus":0.40},
#     {"groups":["authority","money","commitment"],         "bonus":0.35},
#     {"groups":["authority","warrant","urgency"],          "bonus":0.38},
#     {"groups":["threat","money","scarcity"],              "bonus":0.33},
#     {"groups":["distraction","account","authority"],      "bonus":0.30},
#     {"groups":["social_proof","authority","threat"],      "bonus":0.28},
#     {"groups":["reciprocity","commitment","money"],       "bonus":0.28},
#     {"groups":["urgency","scarcity","money"],             "bonus":0.25},
#     {"groups":["distraction","warrant","commitment"],     "bonus":0.25},
#     {"groups":["authority","urgency"],                    "bonus":0.20},
#     {"groups":["authority","money"],                      "bonus":0.20},
#     {"groups":["threat","urgency"],                       "bonus":0.20},
#     {"groups":["account","urgency"],                      "bonus":0.18},
#     {"groups":["distraction","money"],                    "bonus":0.15},
# ]

# danger_keywords = [kw for g in CIALDINI_GROUPS.values() for kw in g["keywords"]]

# # ---------------------------
# # FIX 1 — Generic-only keyword groups
# # These words only score if a non-generic group is also present.
# # Stops "urgent meeting", "send file", "immediately" from triggering alone.
# # ---------------------------
# GENERIC_ONLY_GROUPS = {
#     "urgency":     {"immediately","right now","abhi","turant","jaldi",
#                     "tonight","today only","last date","deadline","act now"},
#     "money":       {"send money","transfer","payment","amount","deposit","pay"},
#     "distraction": {"confidential","sensitive","secret","sealed"},
# }

# # ---------------------------
# # FIX 2 — Safe context: greetings + business phrases never flagged
# # ---------------------------
# SAFE_CONTEXT = {
#     "hello","hi","hey","okay","ok","yes","no","sure","bye","thanks",
#     "thank you","good morning","good night","good evening","happy birthday",
#     "hmm","right","alright","fine","got it","will do","take care","later",
#     "haan","theek hai","bilkul","nahin","shukriya","namaste","achha",
#     "thik hai","chal","koi baat nahi","chalta hai","haan ji","sahi hai",
#     "congrats","congratulations","welcome","no problem","my pleasure",
#     "good","great","nice","wonderful","amazing","fantastic","perfect",
#     "hold on","one second","just a moment","coming","on my way","reached",
#     "sorry","pardon","excuse me","my bad","oops","nevermind","forget it",
#     "see you","catch you later","talk soon","peace","ciao","tata","bye bye",
#     # Business phrases
#     "send file","send the file","send document","urgent meeting",
#     "meeting is urgent","schedule meeting","reschedule meeting",
#     "urgent call","join the call","hop on a call","quick call",
#     "send report","submit report","urgent deadline","project deadline",
#     "urgent update","status update","send update","share update",
#     "urgent request","please send","please share","can you send",
#     "send me","share the","please upload","upload the file",
#     "urgent task","priority task","high priority","top priority",
#     "immediate action","action required","response needed",
#     "reply urgently","respond asap","get back to me","follow up",
#     "quick update","brief update","daily update","weekly update",
#     "team meeting","board meeting","client meeting","sync up",
#     "let us sync","quick sync","touch base","catch up",
# }

# MIN_CONFIDENCE = 0.35
# MIN_TEXT_LEN   = 4


# def is_safe_context(text):
#     """Returns True if text is a short/neutral/business utterance."""
#     text = text.strip()
#     if len(text) < MIN_TEXT_LEN:
#         return True
#     words = set(text.lower().split())
#     if words.issubset(SAFE_CONTEXT):
#         return True
#     if len(words) <= 5 and len(words & SAFE_CONTEXT) / max(len(words), 1) >= 0.7:
#         return True
#     return False


# # ---------------------------
# # FIX 1 — Updated compute_keyword_score
# # Minimum 2 groups required. Generic-only words suppressed without context.
# # ---------------------------
# def compute_keyword_score(text):
#     """
#     Returns (keyword_score capped at 1.0, groups_hit set, combo_name or None).
#     Single keyword never flags — needs minimum 2 Cialdini groups.
#     """
#     text_lower = text.lower()
#     groups_hit = set()

#     for group_name, group_data in CIALDINI_GROUPS.items():
#         for kw in group_data["keywords"]:
#             if kw in text_lower:
#                 groups_hit.add(group_name)
#                 break

#     # Minimum 2 groups required
#     if len(groups_hit) < 2:
#         return 0.0, groups_hit, None

#     # Suppress generic-only groups unless a non-generic group is also present
#     non_generic = groups_hit - set(GENERIC_ONLY_GROUPS.keys())
#     adjusted_groups = set()
#     for gname in groups_hit:
#         if gname in GENERIC_ONLY_GROUPS:
#             hit_kw = next(
#                 (kw for kw in CIALDINI_GROUPS[gname]["keywords"] if kw in text_lower),
#                 None
#             )
#             if hit_kw in GENERIC_ONLY_GROUPS[gname]:
#                 # Generic word — only count if non-generic group present
#                 if len(non_generic) >= 1:
#                     adjusted_groups.add(gname)
#             else:
#                 # Specific scam phrase — always count
#                 adjusted_groups.add(gname)
#         else:
#             adjusted_groups.add(gname)

#     if len(adjusted_groups) < 2:
#         return 0.0, adjusted_groups, None

#     base_score = sum(CIALDINI_GROUPS[g]["score"] for g in adjusted_groups)

#     combo_bonus = 0.0
#     combo_name  = None
#     for combo in COMBINATIONS:
#         if set(combo["groups"]).issubset(adjusted_groups):
#             if combo["bonus"] > combo_bonus:
#                 combo_bonus = combo["bonus"]
#                 combo_name  = "+".join(combo["groups"])

#     return min(base_score + combo_bonus, 1.0), adjusted_groups, combo_name


# # ---------------------------
# # Negation / joke context — suppress scoring if these appear
# # Handles "I wanna arrest you just joking", casual money requests etc.
# # ---------------------------
# NEGATION_PHRASES = {
#     "just joking","just kidding","i'm joking","i am joking","i'm kidding",
#     "i am kidding","just a joke","only joking","only kidding","it's a prank",
#     "its a prank","just playing","i was joking","i was kidding",
#     "haha","lol","lmao","just messing","just testing",
#     "mazak kar raha","mazak tha","joke kar raha","bas mazak",
#     "kidding yaar","joking yaar","timepass","fun mein bola",
# }

# def has_negation(text):
#     """Returns True if text contains joke/negation phrases."""
#     text_lower = text.lower()
#     return any(phrase in text_lower for phrase in NEGATION_PHRASES)


# def get_context_text(new_text, window, max_window=2):
#     """
#     Combines recent transcript chunks for context-aware scam detection.
#     """
#     window.append(new_text)

#     if len(window) > max_window:
#         window.pop(0)

#     return " ".join(window)


# # ---------------------------
# # Emotion Detection
# # ---------------------------
# EMOTION_PATTERNS = {
#     "FEAR": {
#         "keywords": ["scared","afraid","please don't","ghabrana","dar gaya","dar gayi",
#                      "bachao","please help","mercy","begging","frighten"],
#         "color": "emo-fear", "icon": "😨"
#     },
#     "ANGER": {
#         "keywords": ["how dare","this is wrong","illegal","unfair","gussa","galat hai",
#                      "yeh sahi nahi","protest","refuse","nahi maanunga"],
#         "color": "emo-anger", "icon": "😠"
#     },
#     "URGENCY": {
#         "keywords": ["immediately","right now","abhi","turant","urgent","jaldi",
#                      "no time","last chance","aakhri mauka","within hours","within minutes"],
#         "color": "emo-urgency", "icon": "⚡"
#     },
#     "COERCION": {
#         "keywords": ["you must","you have to","aapko karna hoga","comply","mandatory",
#                      "or else","warna","otherwise","no choice","forced"],
#         "color": "emo-coerce", "icon": "🔒"
#     },
#     "CALM": {
#         "keywords": ["relax","don't worry","safe","theek hai","koi baat nahi",
#                      "all good","fine","no problem","sab theek"],
#         "color": "emo-calm", "icon": "😌"
#     },
# }

# def detect_emotions(text):
#     text_l = text.lower()
#     detected = []
#     for emotion, data in EMOTION_PATTERNS.items():
#         for kw in data["keywords"]:
#             if kw in text_l:
#                 detected.append((emotion, data["color"], data["icon"]))
#                 break
#     return detected

# # ─────────────────────────────────────────────────────────────────────────────
# # VICTIM COMPLIANCE SCORING ENGINE
# # Theoretical basis:
# #   Cialdini (1984) — Influence: The Psychology of Persuasion
# #   Milgram (1963)  — Obedience to Authority (65% compliance to authority)
# #   Workman (2008)  — Situational social influence and human behavior
# #   Ferreira (2015) — Principles of Persuasion in Social Engineering
# #   Vishwanath (2018) — Suspicion Cognition and Automaticity Model (SCAM)
# #
# # Core insight: compliance is NOT uniform — it depends on WHICH Cialdini
# # principle the attacker used. Each principle triggers a different
# # psychological response pathway in the victim.
# # ─────────────────────────────────────────────────────────────────────────────

# VICTIM_RESPONSE_SIGNALS = {

#     # DEFERENCE — triggered by Authority principle
#     # Milgram (1963): 65% of people obey authority unconditionally
#     "deference": {
#         "phrases": [
#             "yes sir","yes officer","yes ma'am","okay sir","ji haan","haan sir",
#             "ji officer","samajh gaya","theek hai sir","ji bilkul","zaroor sir",
#             "as you say","i understand officer","whatever you say","i'll cooperate",
#             "i will cooperate","cooperate karunga","cooperate karenge",
#             "aap sahi keh rahe","mujhe maafi","i'm sorry sir","of course officer",
#         ],
#         "base_weight": 0.45,
#         "triggered_by": ["authority","warrant"],
#     },

#     # PANIC COMPLIANCE — triggered by Urgency + Scarcity + Threat
#     # Vishwanath (2018): time pressure disables analytical thinking
#     "panic": {
#         "phrases": [
#             "okay okay","what do i do","what should i do","kya karun","kya karoon",
#             "please help","tell me what to do","jaldi batao","abhi kya karun",
#             "i'll do it","kar deta hoon","kar deti hoon","yes yes",
#             "okay i'm doing it","i'm transferring","sending now","bhej raha hoon",
#             "please don't arrest","ghabra gaya","ghabra gayi","i'm scared",
#             "dar lag raha","please don't","mujhe kya karna","i'm confused",
#         ],
#         "base_weight": 0.40,
#         "triggered_by": ["urgency","scarcity","threat"],
#     },

#     # OBLIGATORY COMPLIANCE — triggered by Reciprocity
#     # Cialdini: reciprocity creates psychological debt
#     "obligatory": {
#         "phrases": [
#             "thank you for telling me","thank you for informing","thanks for warning",
#             "i appreciate","batane ke liye shukriya","shukriya","dhanyavaad",
#             "you're helping me","i know you're trying to help","i'll do as you say",
#             "aap ne bataya isliye","aapka shukriya","aap sahi keh rahe hain",
#         ],
#         "base_weight": 0.30,
#         "triggered_by": ["reciprocity"],
#     },

#     # CONSISTENCY COMPLIANCE — triggered by Commitment
#     # Cialdini: once committed, people feel pressure to stay consistent
#     "consistency": {
#         "phrases": [
#             "i said i would","i already said","maine kaha tha","haan maine kaha",
#             "i'm not going back","i'll keep my word","i said yes","i agreed",
#             "yes i'll do it","i won't back out","as i said","jaise maine kaha",
#         ],
#         "base_weight": 0.25,
#         "triggered_by": ["commitment"],
#     },

#     # INFORMATION DISCLOSURE — any principle, highest risk signal
#     # Vishwanath: info disclosure = victim crossed point of no return
#     "info_leak": {
#         "phrases": [
#             "my account number","my otp is","my pin is","my card number",
#             "cvv is","aadhaar is","pan number","date of birth is",
#             "otp aaya","otp share","pin batata","mera account number",
#             "mera otp","meri id","card number hai","details de deta",
#             "password","net banking","login id","user id","my address is",
#         ],
#         "base_weight": 0.70,
#         "triggered_by": ["account","authority","urgency"],
#     },

#     # RESISTANCE — victim pushing back (NEGATIVE compliance)
#     "resistance": {
#         "phrases": [
#             "no","i won't","i refuse","this is a scam","you are a fraud",
#             "i'm calling police","calling my lawyer","i don't believe you",
#             "nahi karunga","nahi karungi","fraud hai","scam hai",
#             "police bulata hoon","fake call","i'm hanging up","who are you really",
#             "prove it","show me your id","i need proof","verify yourself",
#             "mujhe nahi karna","jhooth bol rahe","aap fraud hain",
#         ],
#         "base_weight": -0.40,
#         "triggered_by": [],
#     },
# }

# # When attacker's principle matches victim's response type — amplify score
# # (Cialdini's manipulation is "working" as intended)
# PRINCIPLE_AMPLIFIERS = {
#     ("authority",   "deference"):   1.4,   # Milgram: strongest obedience pathway
#     ("urgency",     "panic"):       1.3,   # System 2 shutdown
#     ("scarcity",    "panic"):       1.2,
#     ("reciprocity", "obligatory"):  1.3,   # psychological debt fulfilled
#     ("commitment",  "consistency"): 1.2,   # foot-in-the-door working
#     ("threat",      "panic"):       1.35,  # fight-or-flight override
#     ("money",       "info_leak"):   1.5,   # financial coercion + disclosure
#     ("account",     "info_leak"):   1.6,   # credential request + disclosure = critical
# }


# def score_victim_response(victim_text, attacker_groups_hit, last_attacker_score):
#     """
#     Score victim response relative to which Cialdini principle the attacker used.
#     Returns (compliance_score float -1.0 to 1.0, response_type str)
#     """
#     if not victim_text or not victim_text.strip():
#         return 0.0, "neutral"

#     text_lower = victim_text.lower()
#     best_score = 0.0
#     best_type  = "neutral"

#     for response_type, data in VICTIM_RESPONSE_SIGNALS.items():
#         for phrase in data["phrases"]:
#             if phrase in text_lower:
#                 raw_weight = data["base_weight"]

#                 # Amplify if attacker's active principle matches this response type
#                 amplifier = 1.0
#                 for attacker_group in attacker_groups_hit:
#                     key = (attacker_group, response_type)
#                     if key in PRINCIPLE_AMPLIFIERS:
#                         amplifier = max(amplifier, PRINCIPLE_AMPLIFIERS[key])

#                 weighted = raw_weight * amplifier

#                 # Scale by attacker sentence danger level
#                 if last_attacker_score > 0.6:
#                     weighted *= 1.3
#                 elif last_attacker_score > 0.38:
#                     weighted *= 1.1

#                 if abs(weighted) > abs(best_score):
#                     best_score = weighted
#                     best_type  = response_type
#                 break

#     return round(min(max(best_score, -1.0), 1.0), 3), best_type


# def analyse_full_conversation(conversation):
#     """
#     Final conversation-level fraud analysis.
#     Formula based on Ferreira (2015) + Vishwanath (2018):
#       final = 0.40 * avg_attacker_score
#             + 0.35 * victim_compliance
#             + 0.10 * escalation_pattern
#             + 0.15 * (peak_risk + critical_signals)
#             + trajectory_bonus - resistance_penalty
#     """
#     from collections import Counter
#     if not conversation:
#         return None

#     attacker_turns = [t for t in conversation if t["speaker"] == "attacker"]
#     victim_turns   = [t for t in conversation if t["speaker"] == "victim"]

#     if not attacker_turns:
#         return None

#     attacker_scores = [t["score"] for t in attacker_turns]
#     avg_attacker    = sum(attacker_scores) / len(attacker_scores)
#     peak_attacker   = max(attacker_scores)

#     compliance_scores = [t.get("compliance_score", 0.0) for t in victim_turns]
#     if compliance_scores:
#         avg_compliance = sum(compliance_scores) / len(compliance_scores)
#         if len(compliance_scores) >= 3:
#             mid = len(compliance_scores) // 2
#             first_half  = compliance_scores[:mid]
#             second_half = compliance_scores[mid:]
#             trajectory_bonus = (sum(second_half)/len(second_half)
#                               - sum(first_half)/len(first_half)) * 0.15
#         else:
#             trajectory_bonus = 0.0
#     else:
#         avg_compliance   = 0.0
#         trajectory_bonus = 0.0

#     # Escalation: max consecutive positive compliances (foot-in-the-door)
#     max_consecutive = current_streak = 0
#     for t in victim_turns:
#         if t.get("compliance_score", 0) > 0.15:
#             current_streak += 1
#             max_consecutive = max(max_consecutive, current_streak)
#         else:
#             current_streak = 0
#     escalation_score = min(max_consecutive * 0.08, 0.30)

#     info_disclosed   = any(t.get("response_type") == "info_leak" for t in victim_turns)
#     critical_bonus   = 0.35 if info_disclosed else 0.0

#     resistance_count   = sum(1 for t in victim_turns if t.get("response_type") == "resistance")
#     resistance_penalty = min(resistance_count * 0.10, 0.25)

#     raw = (
#         0.40 * avg_attacker
#         + 0.35 * max(avg_compliance, 0)
#         + 0.10 * escalation_score
#         + 0.15 * (peak_attacker * 0.5 + critical_bonus * 0.5)
#         + trajectory_bonus
#         - resistance_penalty
#     )
#     final_score = round(min(max(raw, 0.0), 1.0), 3)

#     if info_disclosed:
#         verdict, color = "CRITICAL — Information Disclosed", "#cc0000"
#     elif final_score > 0.65:
#         verdict, color = "HIGH FRAUD RISK", "#cc0000"
#     elif final_score > 0.40:
#         verdict, color = "SUSPICIOUS CONVERSATION", "#ff8800"
#     elif final_score > 0.20:
#         verdict, color = "LOW RISK — Monitor", "#ffcc00"
#     else:
#         verdict, color = "SAFE CONVERSATION", "#00cc55"

#     all_groups = []
#     for t in attacker_turns:
#         all_groups.extend(list(t.get("groups", set())))
#     dominant = [g for g, _ in Counter(all_groups).most_common(3)]

#     return {
#         "final_score":         final_score,
#         "verdict":             verdict,
#         "color":               color,
#         "avg_attacker":        round(avg_attacker, 3),
#         "peak_attacker":       round(peak_attacker, 3),
#         "avg_compliance":      round(avg_compliance, 3),
#         "escalation_score":    round(escalation_score, 3),
#         "critical_bonus":      critical_bonus,
#         "resistance_penalty":  round(resistance_penalty, 3),
#         "trajectory_bonus":    round(trajectory_bonus, 3),
#         "info_disclosed":      info_disclosed,
#         "dominant_principles": dominant,
#         "attacker_turns":      len(attacker_turns),
#         "victim_turns":        len(victim_turns),
#     }

# # ---------------------------
# # Session State
# # ---------------------------
# defaults = {
#     "running":           False,
#     "history":           [],
#     "current_score":     0.0,
#     "total_chunks":      0,
#     "high_risk_count":   0,
#     "risk_timeline":     [],
#     "keyword_hit_count": 0,
#     "escalation_bonus":  0.0,
#     "transcript_window": [],
#     # ── Two-speaker conversation system ──
#     "turn":              "attacker",   # current turn: "attacker" or "victim"
#     "conversation":      [],           # full turn log [{speaker, text, score, ...}]
#     "last_attacker_score":   0.0,
#     "last_attacker_groups":  set(),
#     "consecutive_compliances": 0,
#     "final_analysis_done": False,      # whether final analysis has run
#     "record_attacker": False,
#     "record_victim": False,
#     "final_result":      None,         # stores final conversation analysis result
# }
# for k, v in defaults.items():
#     if k not in st.session_state:
#         st.session_state[k] = v

# # ---------------------------
# # Header
# # ---------------------------
# st.markdown("""
# <div class="main-header">
#     <h1>🛡️ SCAM SHIELD</h1>
#     <div class="subtitle">Real-Time Digital Arrest Scam Detection System</div>
# </div>
# """, unsafe_allow_html=True)

# left_col, right_col = st.columns([3, 2], gap="large")

# # ════════════════════════════════════════════
# # LEFT COLUMN
# # ════════════════════════════════════════════
# with left_col:
#     # ── Row 1: Start Call + End Call ──
#     c1, c2 = st.columns(2)
#     with c1:
#         start_btn = st.button("▶  START CALL", type="primary", use_container_width=True)
#     with c2:
#         stop_btn  = st.button("📵  END CALL", type="secondary", use_container_width=True)

#     # ── Row 2: Attacker record + Victim record ──
#     c3, c4 = st.columns(2)
#     with c3:
#         attacker_btn = st.button("🔴  RECORD ATTACKER", use_container_width=True)
#         if attacker_btn:
#             st.session_state.record_attacker = True
#     with c4:
#         victim_btn   = st.button("🟢  RECORD VICTIM",   use_container_width=True)
#         if victim_btn:
#             st.session_state.record_victim = True

#     # ── Row 3: Final analysis button ──
#     analyse_btn = st.button("🧠  CALCULATE FINAL FRAUD RISK",
#                             use_container_width=True,
#                             type="primary" if st.session_state.conversation else "secondary")

#     if start_btn:
#         st.session_state.running               = True
#         st.session_state.conversation          = []
#         st.session_state.history               = []
#         st.session_state.risk_timeline         = []
#         st.session_state.current_score         = 0.0
#         st.session_state.total_chunks          = 0
#         st.session_state.high_risk_count       = 0
#         st.session_state.escalation_bonus      = 0.0
#         st.session_state.keyword_hit_count     = 0
#         st.session_state.transcript_window     = []
#         st.session_state.last_attacker_score   = 0.0
#         st.session_state.last_attacker_groups  = set()
#         st.session_state.consecutive_compliances = 0
#         st.session_state.final_analysis_done   = False
#         st.session_state.final_result          = None
#         st.session_state.turn                  = "attacker"

#     if stop_btn:
#         st.session_state.running           = False
#         st.session_state.escalation_bonus  = 0.0
#         st.session_state.keyword_hit_count = 0
#         st.session_state.current_score     = 0.0
#         st.session_state.transcript_window = []

#     if analyse_btn and len(st.session_state.conversation) >= 2:
#         try:
#             predictor = ConversationPredictor()
#             result    = predictor.predict(st.session_state.conversation)
#             st.session_state.final_result        = result
#             st.session_state.final_analysis_done = True
#         except Exception as e:
#             # Fallback to rule-based if model not yet trained
#             result = analyse_full_conversation(st.session_state.conversation)
#             st.session_state.final_result        = result
#             st.session_state.final_analysis_done = True
#             st.session_state.final_result["_fallback"] = True

#     mic_ph  = st.empty()
#     wave_ph = st.empty()

#     def render_mic(active=False):
#         cls  = "mic-btn active" if active else "mic-btn"
#         lcls = "mic-label active" if active else "mic-label"
#         mic_ph.markdown(
#             f'<div class="mic-wrapper">'
#             f'<div class="{cls}">🎙️</div>'
#             f'<div class="{lcls}">{"LISTENING" if active else "READY"}</div>'
#             f'</div>', unsafe_allow_html=True)

#     def render_soundwave(active=False):
#         cls = "soundwave" if active else "soundwave idle"
#         wave_ph.markdown(
#             f'<div class="{cls}">' + ''.join(['<div class="bar"></div>']*9) + '</div>',
#             unsafe_allow_html=True)

#     render_mic(False)
#     render_soundwave(False)

#     m1, m2, m3, m4 = st.columns(4)
#     mp = [m1.empty(), m2.empty(), m3.empty(), m4.empty()]

#     def render_metrics():
#         sp = int(st.session_state.current_score * 100)
#         sc = "red" if sp > 38 else ("orange" if sp > 22 else "green")
#         rc = "red" if st.session_state.high_risk_count > 0 else "green"
#         eb = int(st.session_state.escalation_bonus * 100)
#         ec = "red" if eb > 20 else "orange" if eb > 10 else "green"
#         mp[0].markdown(f'<div class="metric-box"><div class="metric-label">Chunks</div><div class="metric-value">{st.session_state.total_chunks}</div></div>', unsafe_allow_html=True)
#         mp[1].markdown(f'<div class="metric-box"><div class="metric-label">High Risk</div><div class="metric-value {rc}">{st.session_state.high_risk_count}</div></div>', unsafe_allow_html=True)
#         mp[2].markdown(f'<div class="metric-box"><div class="metric-label">Risk %</div><div class="metric-value {sc}">{sp}%</div></div>', unsafe_allow_html=True)
#         mp[3].markdown(f'<div class="metric-box"><div class="metric-label">Escalation</div><div class="metric-value {ec}">+{eb}%</div></div>', unsafe_allow_html=True)

#     render_metrics()

#     gauge_ph      = st.empty()
#     status_ph     = st.empty()
#     emotion_ph    = st.empty()
#     transcript_ph = st.empty()
#     detail_ph     = st.empty()
#     timeline_ph   = st.empty()

#     def render_gauge(score, key="gauge"):
#         val = score * 100
#         if val > 38:
#             bc, nc = "#cc0000", "#ff2200"
#             steps = [('#001a06',0,22),('#1a0c00',22,38),('#2a0000',38,100)]
#         elif val > 22:
#             bc, nc = "#cc6600", "#ff8800"
#             steps = [('#001a06',0,22),('#1a0c00',22,38),('#1a0000',38,100)]
#         else:
#             bc, nc = "#00aa44", "#00cc55"
#             steps = [('#001a06',0,22),('#0a1a00',22,38),('#180000',38,100)]

#         fig = go.Figure(go.Indicator(
#             mode="gauge+number",
#             value=val,
#             number={'suffix':"%",'font':{'color':bc,'size':24,'family':'Share Tech Mono'}},
#             title={'text':"FRAUD RISK",'font':{'color':'#2a3044','size':9,'family':'Share Tech Mono'}},
#             gauge={
#                 'axis':{'range':[0,100],'tickcolor':'#131827',
#                         'tickfont':{'color':'#2a3044','size':8},'tickwidth':1},
#                 'bar':{'color':bc,'thickness':0.2},
#                 'bgcolor':'#0b0e1a','borderwidth':0,
#                 'steps':[{'range':[s[1],s[2]],'color':s[0]} for s in steps],
#                 'threshold':{'line':{'color':nc,'width':3},'thickness':0.8,'value':val}
#             }
#         ))
#         fig.update_layout(
#             paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
#             font={'color':'#d0d8f0'}, height=190,
#             margin=dict(t=26, b=4, l=10, r=10)
#         )
#         gauge_ph.plotly_chart(fig, use_container_width=True, key=key)

#     def render_timeline():
#         tl = st.session_state.risk_timeline
#         if len(tl) < 2:
#             timeline_ph.markdown(
#                 '<div class="section-title" style="margin-top:5px;">📈 RISK ESCALATION TIMELINE</div>'
#                 '<div style="color:#2a3044;font-family:Share Tech Mono,monospace;'
#                 'font-size:0.65rem;text-align:center;padding:10px 0;">AWAITING DATA...</div>',
#                 unsafe_allow_html=True)
#             return

#         times  = [t[0] for t in tl]
#         scores = [t[1]*100 for t in tl]
#         colors = ["#cc0000" if s > 38 else "#ff8800" if s > 22 else "#00cc55" for s in scores]

#         fig = go.Figure()
#         fig.add_hrect(y0=0,  y1=22,  fillcolor="rgba(0,204,85,0.06)",  line_width=0)
#         fig.add_hrect(y0=22, y1=38,  fillcolor="rgba(255,136,0,0.06)", line_width=0)
#         fig.add_hrect(y0=38, y1=100, fillcolor="rgba(204,0,0,0.07)",   line_width=0)
#         fig.add_trace(go.Scatter(
#             x=times, y=scores,
#             mode='lines+markers',
#             line=dict(color='#1e6fff', width=2),
#             marker=dict(color=colors, size=7, line=dict(color='#06080f', width=1)),
#             fill='tozeroy',
#             fillcolor='rgba(30,111,255,0.07)'
#         ))
#         fig.add_hline(y=22, line=dict(color="rgba(255,136,0,0.3)", width=1, dash="dot"))
#         fig.add_hline(y=38, line=dict(color="rgba(204,0,0,0.3)",   width=1, dash="dot"))
#         fig.update_layout(
#             paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
#             height=130,
#             margin=dict(t=8, b=22, l=30, r=10),
#             xaxis=dict(showgrid=False, tickfont=dict(color='#2a3044', size=8),
#                        tickangle=-30, color='#2a3044'),
#             yaxis=dict(showgrid=False, range=[0,100],
#                        tickfont=dict(color='#2a3044', size=8),
#                        tickvals=[0,22,38,100], color='#2a3044'),
#             showlegend=False
#         )
#         timeline_ph.markdown(
#             '<div class="section-title" style="margin-top:5px;">📈 RISK ESCALATION TIMELINE</div>',
#             unsafe_allow_html=True)
#         timeline_ph.plotly_chart(fig, use_container_width=True,
#                                  key=f"timeline_{len(tl)}")

#     # Initial render
#     render_gauge(0, key="gauge_init")
#     status_ph.markdown('<div class="status-safe">⬤ &nbsp; SYSTEM READY</div>', unsafe_allow_html=True)
#     emotion_ph.markdown("", unsafe_allow_html=True)
#     transcript_ph.markdown(
#         '<div class="section-title" style="margin-top:4px;">📝 LATEST TRANSCRIPTION</div>'
#         '<div class="transcript-box">Waiting for audio input...</div>',
#         unsafe_allow_html=True)
#     render_timeline()

# # ════════════════════════════════════════════
# # RIGHT COLUMN — Call Log
# # ════════════════════════════════════════════
# with right_col:
#     st.markdown('<div class="section-title" style="margin-bottom:8px;">📋 &nbsp; CALL LOG</div>',
#                 unsafe_allow_html=True)
#     history_ph = st.empty()

#     def render_history():
#         if not st.session_state.history:
#             history_ph.markdown(
#                 '<div style="color:#1a2030;font-family:Share Tech Mono,monospace;'
#                 'font-size:0.68rem;letter-spacing:2px;text-align:center;padding:22px 0;">'
#                 'NO ENTRIES YET</div>', unsafe_allow_html=True)
#         else:
#             html = ""
#             for e in reversed(st.session_state.history[-20:]):
#                 sp = int(e['score'] * 100)
#                 speaker = e.get('speaker', 'attacker')

#                 if speaker == 'victim':
#                     cs = e.get('compliance_score', 0.0)
#                     rt = e.get('response_type', 'neutral')
#                     if rt == 'resistance':
#                         tc, badge = "safe-tag", f"✋ RESISTANT ({round(cs,2)})"
#                     elif rt == 'info_leak':
#                         tc, badge = "danger-tag", f"🚨 INFO LEAKED"
#                     elif cs > 0.3:
#                         tc, badge = "danger-tag", f"⚠ HIGH COMPLIANCE ({round(cs,2)})"
#                     elif cs > 0.1:
#                         tc, badge = "warn-tag", f"⚡ COMPLIANCE ({round(cs,2)})"
#                     else:
#                         tc, badge = "safe-tag", f"✓ NEUTRAL"
#                     speaker_label = '<span style="color:#00cc55;font-size:0.6rem;">🟢 VICTIM</span>'
#                 else:
#                     if e['score'] > 0.38:
#                         tc, badge = "danger-tag", f"⚠ HIGH RISK — {sp}%"
#                     elif e['score'] > 0.22:
#                         tc, badge = "warn-tag",   f"⚡ SUSPICIOUS — {sp}%"
#                     else:
#                         tc, badge = "safe-tag",   f"✓ SAFE — {sp}%"
#                     speaker_label = '<span style="color:#cc0000;font-size:0.6rem;">🔴 ATTACKER</span>'

#                 kw_html = (
#                     f'<div style="font-size:0.62rem;color:#aa0033;margin-top:2px;">'
#                     f'🔑 {", ".join(list(e.get("groups",set()))[:4])}</div>'
#                 ) if e.get("groups") else ""

#                 combo_html = (
#                     f'<div style="font-size:0.62rem;color:#cc0044;margin-top:1px;">'
#                     f'⚡ {e["combo"]}</div>'
#                 ) if e.get("combo") else ""

#                 emo_html = ""
#                 for emo, ecls, eico in e.get('emotions', []):
#                     emo_html += f'<span class="emotion-badge {ecls}">{eico} {emo}</span>'

#                 safe_text = e['text'][:150] + ('...' if len(e['text']) > 150 else '')
#                 html += (
#                     '<div class="history-entry">'
#                     f'<div class="history-time">{e["time"]} &nbsp; {speaker_label}</div>'
#                     f'<div class="history-text">{safe_text}</div>'
#                     f'{kw_html}{combo_html}{emo_html}'
#                     f'<div class="{tc}">{badge}</div>'
#                     '</div>'
#                 )
#             history_ph.markdown(html, unsafe_allow_html=True)

#     render_history()

# # ════════════════════════════════════════════
# # HELPER — shared recording + transcription
# # ════════════════════════════════════════════
# def record_and_transcribe(duration=8, sample_rate=16000):
#     """Record audio and return transcribed text."""
#     audio = sd.rec(int(duration * sample_rate),
#                    samplerate=sample_rate, channels=1, dtype='float32')
#     sd.wait()
#     audio = np.squeeze(audio)

#     # Empty audio protection
#     if audio is None:
#         return ""

#     if len(audio) == 0:
#         return ""

#     # Silence protection
#     if np.max(np.abs(audio)) < 0.001:
#         return ""

#     audio = audio.astype(np.float32)
   

#     write("temp.wav", sample_rate, audio.astype(np.float32))
#     import gc
#     import torch

#     if torch.cuda.is_available():
#         torch.cuda.empty_cache()

    
#     segments, info = whisper_model.transcribe("temp.wav",beam_size=1, vad_filter=True)

#     text = " ".join([segment.text for segment in segments]).strip()

    

#     if not text or len(text.strip()) < 2:
#         return None

#     return text

# def score_attacker_turn(text, chunk_count):
#     """Run full ML + keyword scoring pipeline on attacker text."""
#     if is_safe_context(text):
#         prev = st.session_state.current_score
#         return {
#             "score": prev * 0.4, "probability": 0.0,
#             "keyword_score": 0.0, "groups_hit": set(),
#             "combo_name": None, "emotions": [],
#         }

#     context_text = get_context_text(text, st.session_state.transcript_window)

#     text_vec         = vectorizer.transform([text])
#     kw_score_ml, groups_hit_ml, _ = compute_keyword_score(text)
#     kw_groups_ml     = len(groups_hit_ml)
#     kw_combo_ml      = 1 if kw_score_ml > 0 else 0
#     kw_flags         = [
#         1 if any(kw in text.lower() for kw in CIALDINI_GROUPS[g]["keywords"]) else 0
#         for g in CIALDINI_GROUPS.keys()
#     ]
#     numeric_features = [kw_score_ml, kw_groups_ml, kw_combo_ml] + kw_flags
#     num_vec          = csr_matrix([numeric_features])
#     final_input      = hstack([text_vec, num_vec])
#     probability      = model.predict_proba(final_input)[0][1]

#     if probability < MIN_CONFIDENCE:
#         return {
#             "score": 0.0, "probability": probability,
#             "keyword_score": 0.0, "groups_hit": set(),
#             "combo_name": None, "emotions": [],
#         }

#     keyword_score, groups_hit, combo_name = compute_keyword_score(context_text)

#     hits = len(groups_hit)
#     if hits >= 2:
#         st.session_state.keyword_hit_count += hits
#         st.session_state.escalation_bonus = min(
#             st.session_state.escalation_bonus + 0.04 * hits, 0.35)
#     else:
#         st.session_state.escalation_bonus = max(
#             st.session_state.escalation_bonus - 0.02, 0.0)

#     base_final = min(probability + 0.10 * keyword_score, 1.0)
#     raw_score  = min(base_final + st.session_state.escalation_bonus, 1.0)
#     prev       = st.session_state.current_score
#     new_score  = prev + (raw_score - prev) * (0.8 if raw_score > prev else 0.3)

#     return {
#         "score": new_score, "probability": probability,
#         "keyword_score": keyword_score, "groups_hit": groups_hit,
#         "combo_name": combo_name, "emotions": detect_emotions(text),
#     }


# # ════════════════════════════════════════════
# # ATTACKER RECORDING
# # ════════════════════════════════════════════
# if st.session_state.record_attacker and st.session_state.running:
#     st.session_state.record_attacker = False
#     chunk_count = st.session_state.total_chunks + 1

#     render_mic(True)
#     render_soundwave(True)
#     status_ph.markdown(
#         '<div class="status-listening">🔴 &nbsp; RECORDING ATTACKER...</div>',
#         unsafe_allow_html=True)

#     # text = record_and_transcribe()
#     # st.write("AFTER TRANSCRIBE")

#     # try:
#     #     result = score_attacker_turn(text, chunk_count)
#     #     st.write("SCORING SUCCESS")
#     # except Exception as e:
#     #     st.error(f"SCORING ERROR: {e}")
#     #     raise
#     text = record_and_transcribe()

#     if text:
#         try:
#             result = score_attacker_turn(text, chunk_count)
#         except Exception as e:
#             st.error(f"SCORING ERROR: {e}")
#             st.session_state.record_attacker = False
#     render_soundwave(False)

#     if not text:
#         render_mic(False)
#         status_ph.markdown(
#             '<div class="status-safe">🔇 &nbsp; NO SPEECH DETECTED</div>',
#             unsafe_allow_html=True)
#         st.session_state.record_attacker = False
#     else:
#         # result = score_attacker_turn(text, chunk_count)
#         new_score     = result["score"]
#         probability   = result["probability"]
#         keyword_score = result["keyword_score"]
#         groups_hit    = result["groups_hit"]
#         combo_name    = result["combo_name"]
#         emotions      = result["emotions"]

#         st.session_state.current_score         = new_score
#         st.session_state.total_chunks         += 1
#         st.session_state.last_attacker_score   = new_score
#         st.session_state.last_attacker_groups  = groups_hit
#         if new_score > 0.38:
#             st.session_state.high_risk_count += 1

#         # Save to per-sentence history
#         st.session_state.history.append({
#             'time': datetime.datetime.now().strftime("%H:%M:%S"),
#             'text': text, 'score': new_score,
#             'ml': probability, 'keywords': keyword_score,
#             'groups': list(groups_hit), 'combo': combo_name, 'emotions': emotions,
#             'speaker': 'attacker',
#         })
        
#         # Save to conversation log for final analysis
#         st.session_state.conversation.append({
#             'speaker': 'attacker', 'text': text, 'score': new_score,
#             'groups': groups_hit, 'combo': combo_name,
#             'time': datetime.datetime.now().strftime("%H:%M:%S"),
#         })

#         st.session_state.risk_timeline.append((
#             datetime.datetime.now().strftime("%H:%M:%S"), new_score))

#         render_gauge(new_score, key=f"gauge_{chunk_count}")

#         if new_score > 0.38:
#             status_ph.markdown(
#                 '<div class="status-danger">⚠ &nbsp; HIGH FRAUD RISK — ATTACKER</div>',
#                 unsafe_allow_html=True)
#         elif new_score > 0.22:
#             status_ph.markdown(
#                 '<div class="status-warning">⚡ &nbsp; SUSPICIOUS — ATTACKER</div>',
#                 unsafe_allow_html=True)
#         else:
#             status_ph.markdown(
#                 '<div class="status-safe">✓ &nbsp; ATTACKER — LOW RISK</div>',
#                 unsafe_allow_html=True)

#         render_mic(new_score > 0.22)

#         if emotions:
#             badges = "".join(
#                 f'<span class="emotion-badge {ecls}">{eico} {emo}</span>'
#                 for emo, ecls, eico in emotions)
#             emotion_ph.markdown(
#                 f'<div style="margin:3px 0 4px 0;">{badges}</div>',
#                 unsafe_allow_html=True)
#         else:
#             emotion_ph.markdown("", unsafe_allow_html=True)

#         transcript_ph.markdown(
#             '<div class="section-title" style="margin-top:4px;">🔴 ATTACKER — LATEST</div>'
#             f'<div class="transcript-box">{text}</div>',
#             unsafe_allow_html=True)

#         formula_line = (
#             f'ML({round(probability,2)}) + 0.10×KW({round(keyword_score,2)})'
#             f' + ESC(+{round(st.session_state.escalation_bonus,2)})'
#             f' = {round(new_score,2)}  [thresh:0.38]'
#         )
#         groups_line = ", ".join(sorted(groups_hit)) if groups_hit else "none"
#         combo_line  = f'⚡ COMBO: {combo_name}' if combo_name else ""
#         detail_ph.markdown(
#             f'<div style="font-family:Share Tech Mono,monospace;font-size:0.62rem;'
#             f'color:#2a3044;text-align:center;letter-spacing:1px;margin-top:2px;line-height:1.6;">'
#             f'{formula_line}<br><span style="color:#1a2a44;">Groups: {groups_line}</span>'
#             + (f'<br><span style="color:#cc0044;">{combo_line}</span>' if combo_line else "")
#             + '</div>', unsafe_allow_html=True)

#         render_metrics()
#         render_timeline()
#         with right_col:
#             render_history()
        
        


# # ════════════════════════════════════════════
# # VICTIM RECORDING
# # ════════════════════════════════════════════
# if st.session_state.record_victim and st.session_state.running:
#     st.session_state.record_victim = False

#     render_mic(True)
#     render_soundwave(True)
#     status_ph.markdown(
#         '<div class="status-listening">🟢 &nbsp; RECORDING VICTIM...</div>',
#         unsafe_allow_html=True)

#     text = record_and_transcribe()

    
#     render_soundwave(False)
#     render_mic(False)

#     if not text:
#         status_ph.markdown(
#             '<div class="status-safe">🔇 &nbsp; NO SPEECH DETECTED</div>',
#             unsafe_allow_html=True)
#         st.session_state.record_victim = False
#     else:
#         # Score victim compliance against last attacker turn
#         compliance_score, response_type = score_victim_response(
#             text,
#             st.session_state.get("last_attacker_groups", set()),
#             st.session_state.last_attacker_score
#         )

#         # Escalation tracker
#         if compliance_score > 0.15:
#             st.session_state.consecutive_compliances += 1
#         else:
#             st.session_state.consecutive_compliances = 0

#         # Save to conversation log (no ML score — victim turn)
#         st.session_state.conversation.append({
#                 'speaker': 'victim',
#                 'text': text,
#                 'score': 0.0,
#                 'groups': [],
#                 'combo': None,
#                 'compliance_score': compliance_score,
#                 'response_type': response_type,
#                 'time': datetime.datetime.now().strftime("%H:%M:%S"),
#         })

#         # Show victim turn in call log
#         st.session_state.history.append({
#             'time':             datetime.datetime.now().strftime("%H:%M:%S"),
#             'text':             text,
#             'score':            0.0,
#             'ml':               0.0,
#             'keywords':         0.0,
#             'groups':           set(),
#             'combo':            None,
#             'emotions':         [],
#             'speaker':          'victim',
#             'compliance_score': compliance_score,
#             'response_type':    response_type,
#         })

#         # Compliance badge color
#         if response_type == "resistance":
#             c_color = "#00cc55"
#             c_label = f"✋ RESISTANT ({round(compliance_score,2)})"
#         elif response_type == "info_leak":
#             c_color = "#cc0000"
#             c_label = f"🚨 INFO LEAKED ({round(compliance_score,2)})"
#         elif compliance_score > 0.3:
#             c_color = "#cc0000"
#             c_label = f"⚠ HIGH COMPLIANCE ({round(compliance_score,2)})"
#         elif compliance_score > 0.1:
#             c_color = "#ff8800"
#             c_label = f"⚡ PARTIAL COMPLIANCE ({round(compliance_score,2)})"
#         else:
#             c_color = "#00cc55"
#             c_label = f"✓ NEUTRAL ({round(compliance_score,2)})"

#         transcript_ph.markdown(
#             '<div class="section-title" style="margin-top:4px;">🟢 VICTIM — RESPONSE</div>'
#             f'<div class="transcript-box">{text}</div>',
#             unsafe_allow_html=True)

#         detail_ph.markdown(
#             f'<div style="font-family:Share Tech Mono,monospace;font-size:0.72rem;'
#             f'color:{c_color};text-align:center;letter-spacing:1px;margin-top:4px;">'
#             f'VICTIM COMPLIANCE: {c_label}<br>'
#             f'<span style="color:#2a3044;font-size:0.6rem;">'
#             f'Response Type: {response_type} | '
#             f'Consecutive Compliances: {st.session_state.consecutive_compliances}'
#             f'</span></div>',
#             unsafe_allow_html=True)

#         with right_col:
#             render_history()
        
        


# # ════════════════════════════════════════════
# # FINAL ANALYSIS PANEL
# # ════════════════════════════════════════════
# if st.session_state.final_analysis_done and st.session_state.final_result:
#     r = st.session_state.final_result
#     is_ml = "combined_score" in r    # True = ML predictor, False = fallback
#     score  = r.get("combined_score", r.get("final_score", 0.0))
#     color  = r["color"]
#     is_fallback = r.get("_fallback", False)

#     st.markdown("---")
#     bd = r.get("breakdown", {})

#     title_text = ("DUAL-LAYER ML CONVERSATION ANALYSIS"
#                   if (is_ml and not is_fallback)
#                   else "CONVERSATION ANALYSIS (RULE-BASED FALLBACK)")

#     layer_blocks = ""
#     if is_ml and not is_fallback:
#         layer_blocks = (
#             f'<div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;margin-bottom:12px;">'
#             f'<div style="background:#06080f;border:1px solid #1a2030;border-radius:6px;padding:8px 14px;min-width:110px;">'
#             f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;">LAYER 1</div>'
#             f'<div style="font-size:0.55rem;color:#2a3044;margin-bottom:4px;">SENTENCE ML AVG</div>'
#             f'<div style="font-size:1.1rem;color:#1e6fff;">{int(r["ml1_avg_score"]*100)}%</div></div>'
#             f'<div style="background:#06080f;border:1px solid #1a2030;border-radius:6px;padding:8px 14px;min-width:110px;">'
#             f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;">LAYER 2</div>'
#             f'<div style="font-size:0.55rem;color:#2a3044;margin-bottom:4px;">CONVERSATION ML</div>'
#             f'<div style="font-size:1.1rem;color:#cc0000;">{int(r["ml2_score"]*100)}%</div></div>'
#             f'<div style="background:#06080f;border:1px solid #1a2030;border-radius:6px;padding:8px 14px;min-width:110px;">'
#             f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;">ENSEMBLE</div>'
#             f'<div style="font-size:0.55rem;color:#2a3044;margin-bottom:4px;">0.55xL2 + 0.45xL1</div>'
#             f'<div style="font-size:1.1rem;color:{color};">{int(score*100)}%</div></div>'
#             f'</div>'
#         )

#     info_block = ""
#     if r.get("info_disclosed"):
#         info_block = (
#             f'<div style="color:#cc0000;font-size:0.8rem;font-weight:bold;'
#             f'border:1px solid #cc0000;border-radius:4px;padding:6px;margin-top:6px;">'
#             f'CRITICAL: PERSONAL INFORMATION WAS DISCLOSED</div>'
#         )

#     comp_val = round(r.get("avg_compliance", bd.get("compliance_avg", 0.0)), 2)
#     res_val  = r.get("resistance_count", 0)
#     pri_val  = r.get("num_principles", 0)
#     str_val  = bd.get("max_compliance_streak", 0)
#     dom_str  = ", ".join(r.get("dominant_principles", [])) or "none"
#     atk_t    = bd.get("attacker_turns", r.get("attacker_turns", "?"))
#     vic_t    = bd.get("victim_turns",   r.get("victim_turns",   "?"))

#     st.markdown(
#         f'<div style="font-family:Share Tech Mono,monospace;text-align:center;'
#         f'padding:22px;background:#0b0e1a;border:2px solid {color};'
#         f'border-radius:10px;margin-top:10px;">'
#         f'<div style="font-size:0.65rem;color:#2a3044;letter-spacing:3px;margin-bottom:8px;">{title_text}</div>'
#         f'<div style="font-size:2.2rem;color:{color};text-shadow:0 0 24px {color}55;font-weight:bold;">{int(score*100)}%</div>'
#         f'<div style="font-size:0.95rem;color:{color};letter-spacing:2px;margin:6px 0 14px 0;">{r["verdict"]}</div>'
#         f'{layer_blocks}'
#         f'<div style="display:flex;justify-content:center;gap:18px;flex-wrap:wrap;font-size:0.62rem;color:#2a3044;margin-bottom:10px;">'
#         f'<span>COMPLIANCE: <span style="color:#ff8800">{comp_val}</span></span>'
#         f'<span>RESISTANCE: <span style="color:#00cc55">{res_val}</span></span>'
#         f'<span>PRINCIPLES: <span style="color:#1e6fff">{pri_val}</span></span>'
#         f'<span>STREAK: <span style="color:#ff8800">{str_val}</span></span>'
#         f'</div>'
#         f'<div style="font-size:0.62rem;color:#2a3044;margin-bottom:8px;">'
#         f'Dominant principles: <span style="color:#1e6fff">{dom_str}</span>'
#         f' &nbsp;|&nbsp; Turns: <span style="color:#cc0000">{atk_t}</span> attacker / '
#         f'<span style="color:#00cc55">{vic_t}</span> victim</div>'
#         f'{info_block}</div>',
#         unsafe_allow_html=True
#     )




import streamlit as st
from faster_whisper import WhisperModel
import joblib
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import plotly.graph_objects as go
import plotly.express as px
import time
import datetime
from scipy.sparse import hstack, csr_matrix

# Import conversation-level predictor (Layer 2)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from predict_conversation import ConversationPredictor
    CONV_MODEL_AVAILABLE = True
except Exception:
    CONV_MODEL_AVAILABLE = False

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

# ---------------------------
# Load Models
# ---------------------------
@st.cache_resource(show_spinner=False)
def load_models():
    wm = WhisperModel("base", device="cpu", compute_type="int8")
    m  = joblib.load("models/scam_model.pkl")
    v  = joblib.load("models/vectorizer.pkl")
    return wm, m, v

whisper_model, model, vectorizer = load_models()


# ---------------------------
# Cialdini Keyword Groups
# ---------------------------
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
            "national security","media blackout","nda sign karo",
            "do not tell anyone","kisi ko mat batao","keep this confidential",
            "do not contact lawyer","do not inform family",
            "this is a secret operation","sub judice matter",
            "sensitive case","high profile matter","sealed envelope",
            "stay on the line","do not hang up","do not disconnect",
            "aap monitored hain","call record ho rahi hai",
            "yeh recorded call hai","evidence ke roop mein",
        ]
    },
    "social_proof": {
        "score": 0.20,
        "keywords": [
            "multiple complaints against you","47 complaints",
            "23 complaints","witnesses against you","3 witnesses",
            "your neighbor reported","your employee reported",
            "your business partner named you","your friend is a witness",
            "your family member named","anonymous complaint",
            "whistleblower aayi hai","gawah hain aapke khilaf",
            "3 independent witnesses","complaints received",
            "national portal par complaints","public complaints",
        ]
    },
    "commitment": {
        "score": 0.20,
        "keywords": [
            "you already agreed","you said you would cooperate",
            "stay on call","remain on line","do not move from location",
            "you have acknowledged","legal obligation","legally bound",
            "mandatory compliance","you must cooperate",
            "aap agree kar chuke hain","aapko cooperate karna hoga",
            "aap legally bound hain","aapko comply karna hoga",
            "aap pe legal obligation hai","undertaking sign karni hogi",
            "affidavit deni hogi","you are obligated","cooperation mandatory",
        ]
    },
}

COMBINATIONS = [
    {"groups":["commitment","reciprocity","distraction"], "bonus":0.35},
    {"groups":["authority","urgency","threat"],           "bonus":0.40},
    {"groups":["authority","money","commitment"],         "bonus":0.35},
    {"groups":["authority","warrant","urgency"],          "bonus":0.38},
    {"groups":["threat","money","scarcity"],              "bonus":0.33},
    {"groups":["distraction","account","authority"],      "bonus":0.30},
    {"groups":["social_proof","authority","threat"],      "bonus":0.28},
    {"groups":["reciprocity","commitment","money"],       "bonus":0.28},
    {"groups":["urgency","scarcity","money"],             "bonus":0.25},
    {"groups":["distraction","warrant","commitment"],     "bonus":0.25},
    {"groups":["authority","urgency"],                    "bonus":0.20},
    {"groups":["authority","money"],                      "bonus":0.20},
    {"groups":["threat","urgency"],                       "bonus":0.20},
    {"groups":["account","urgency"],                      "bonus":0.18},
    {"groups":["distraction","money"],                    "bonus":0.15},
]

danger_keywords = [kw for g in CIALDINI_GROUPS.values() for kw in g["keywords"]]

GENERIC_ONLY_GROUPS = {
    "urgency":     {"immediately","right now","abhi","turant","jaldi",
                    "tonight","today only","last date","deadline","act now"},
    "money":       {"send money","transfer","payment","amount","deposit","pay"},
    "distraction": {"confidential","sensitive","secret","sealed"},
}

SAFE_CONTEXT = {
    "hello","hi","hey","okay","ok","yes","no","sure","bye","thanks",
    "thank you","good morning","good night","good evening","happy birthday",
    "hmm","right","alright","fine","got it","will do","take care","later",
    "haan","theek hai","bilkul","nahin","shukriya","namaste","achha",
    "thik hai","chal","koi baat nahi","chalta hai","haan ji","sahi hai",
    "congrats","congratulations","welcome","no problem","my pleasure",
    "good","great","nice","wonderful","amazing","fantastic","perfect",
    "hold on","one second","just a moment","coming","on my way","reached",
    "sorry","pardon","excuse me","my bad","oops","nevermind","forget it",
    "see you","catch you later","talk soon","peace","ciao","tata","bye bye",
    "send file","send the file","send document","urgent meeting",
    "meeting is urgent","schedule meeting","reschedule meeting",
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
            hit_kw = next(
                (kw for kw in CIALDINI_GROUPS[gname]["keywords"] if kw in text_lower),
                None
            )
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

    combo_bonus = 0.0
    combo_name  = None
    for combo in COMBINATIONS:
        if set(combo["groups"]).issubset(adjusted_groups):
            if combo["bonus"] > combo_bonus:
                combo_bonus = combo["bonus"]
                combo_name  = "+".join(combo["groups"])

    return min(base_score + combo_bonus, 1.0), adjusted_groups, combo_name


NEGATION_PHRASES = {
    "just joking","just kidding","i'm joking","i am joking","i'm kidding",
    "i am kidding","just a joke","only joking","only kidding","it's a prank",
    "its a prank","just playing","i was joking","i was kidding",
    "haha","lol","lmao","just messing","just testing",
    "mazak kar raha","mazak tha","joke kar raha","bas mazak",
    "kidding yaar","joking yaar","timepass","fun mein bola",
}

def has_negation(text):
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in NEGATION_PHRASES)


def get_context_text(new_text, window, max_window=2):
    window.append(new_text)
    if len(window) > max_window:
        window.pop(0)
    return " ".join(window)


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


def score_victim_response(victim_text, attacker_groups_hit, last_attacker_score):
    if not victim_text or not victim_text.strip():
        return 0.0, "neutral"

    text_lower = victim_text.lower()
    best_score = 0.0
    best_type  = "neutral"

    for response_type, data in VICTIM_RESPONSE_SIGNALS.items():
        for phrase in data["phrases"]:
            if phrase in text_lower:
                raw_weight = data["base_weight"]
                amplifier = 1.0
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

    attacker_scores = [t["score"] for t in attacker_turns]
    avg_attacker    = sum(attacker_scores) / len(attacker_scores)
    peak_attacker   = max(attacker_scores)

    compliance_scores = [t.get("compliance_score", 0.0) for t in victim_turns]
    if compliance_scores:
        avg_compliance = sum(compliance_scores) / len(compliance_scores)
        if len(compliance_scores) >= 3:
            mid = len(compliance_scores) // 2
            first_half  = compliance_scores[:mid]
            second_half = compliance_scores[mid:]
            trajectory_bonus = (sum(second_half)/len(second_half)
                              - sum(first_half)/len(first_half)) * 0.15
        else:
            trajectory_bonus = 0.0
    else:
        avg_compliance   = 0.0
        trajectory_bonus = 0.0

    max_consecutive = current_streak = 0
    for t in victim_turns:
        if t.get("compliance_score", 0) > 0.15:
            current_streak += 1
            max_consecutive = max(max_consecutive, current_streak)
        else:
            current_streak = 0
    escalation_score = min(max_consecutive * 0.08, 0.30)

    info_disclosed   = any(t.get("response_type") == "info_leak" for t in victim_turns)
    critical_bonus   = 0.35 if info_disclosed else 0.0

    resistance_count   = sum(1 for t in victim_turns if t.get("response_type") == "resistance")
    resistance_penalty = min(resistance_count * 0.10, 0.25)

    raw = (
        0.40 * avg_attacker
        + 0.35 * max(avg_compliance, 0)
        + 0.10 * escalation_score
        + 0.15 * (peak_attacker * 0.5 + critical_bonus * 0.5)
        + trajectory_bonus
        - resistance_penalty
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
        all_groups.extend(list(t.get("groups", set())))
    dominant = [g for g, _ in Counter(all_groups).most_common(3)]

    return {
        "final_score":         final_score,
        "verdict":             verdict,
        "color":               color,
        "avg_attacker":        round(avg_attacker, 3),
        "peak_attacker":       round(peak_attacker, 3),
        "avg_compliance":      round(avg_compliance, 3),
        "escalation_score":    round(escalation_score, 3),
        "critical_bonus":      critical_bonus,
        "resistance_penalty":  round(resistance_penalty, 3),
        "trajectory_bonus":    round(trajectory_bonus, 3),
        "info_disclosed":      info_disclosed,
        "dominant_principles": dominant,
        "attacker_turns":      len(attacker_turns),
        "victim_turns":        len(victim_turns),
    }

# ---------------------------
# Session State
# ---------------------------
defaults = {
    "running":           False,
    "history":           [],
    "current_score":     0.0,
    "total_chunks":      0,
    "high_risk_count":   0,
    "risk_timeline":     [],
    "keyword_hit_count": 0,
    "escalation_bonus":  0.0,
    "transcript_window": [],
    "turn":              "attacker",
    "conversation":      [],
    "last_attacker_score":   0.0,
    "last_attacker_groups":  set(),
    "consecutive_compliances": 0,
    "final_analysis_done": False,
    "record_attacker": False,
    "record_victim": False,
    "final_result":      None,
    # ── FIX: flag to trigger analyse on next rerun ──
    "trigger_analyse":   False,
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
        start_btn = st.button("▶  START CALL", type="primary", use_container_width=True)
    with c2:
        stop_btn  = st.button("📵  END CALL", type="secondary", use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        attacker_btn = st.button("🔴  RECORD ATTACKER", use_container_width=True)
        if attacker_btn:
            st.session_state.record_attacker = True
    with c4:
        victim_btn   = st.button("🟢  RECORD VICTIM",   use_container_width=True)
        if victim_btn:
            st.session_state.record_victim = True

    # ── FIX: Set a flag on click instead of running analysis inline ──
    analyse_btn = st.button(
        "🧠  CALCULATE FINAL FRAUD RISK",
        use_container_width=True,
        type="primary" if st.session_state.conversation else "secondary"
    )
    if analyse_btn:
        if len(st.session_state.conversation) >= 2:
            st.session_state.trigger_analyse = True
        else:
            st.warning("⚠️ Need at least one attacker turn and one victim turn before analysing.")

    if start_btn:
        st.session_state.running               = True
        st.session_state.conversation          = []
        st.session_state.history               = []
        st.session_state.risk_timeline         = []
        st.session_state.current_score         = 0.0
        st.session_state.total_chunks          = 0
        st.session_state.high_risk_count       = 0
        st.session_state.escalation_bonus      = 0.0
        st.session_state.keyword_hit_count     = 0
        st.session_state.transcript_window     = []
        st.session_state.last_attacker_score   = 0.0
        st.session_state.last_attacker_groups  = set()
        st.session_state.consecutive_compliances = 0
        st.session_state.final_analysis_done   = False
        st.session_state.final_result          = None
        st.session_state.trigger_analyse       = False
        st.session_state.turn                  = "attacker"

    if stop_btn:
        st.session_state.running           = False
        st.session_state.escalation_bonus  = 0.0
        st.session_state.keyword_hit_count = 0
        st.session_state.current_score     = 0.0
        st.session_state.transcript_window = []

    # ── FIX: Run analysis when flag is set (outside button click context) ──
    if st.session_state.trigger_analyse and len(st.session_state.conversation) >= 2:
        st.session_state.trigger_analyse = False
        try:
            predictor = ConversationPredictor()
            result    = predictor.predict(st.session_state.conversation)
            st.session_state.final_result        = result
            st.session_state.final_analysis_done = True
        except Exception as e:
            result = analyse_full_conversation(st.session_state.conversation)
            if result:
                st.session_state.final_result        = result
                st.session_state.final_analysis_done = True
                st.session_state.final_result["_fallback"] = True
            else:
                st.error(f"Analysis failed: {e}")

    mic_ph  = st.empty()
    wave_ph = st.empty()

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

    m1, m2, m3, m4 = st.columns(4)
    mp = [m1.empty(), m2.empty(), m3.empty(), m4.empty()]

    def render_metrics():
        sp = int(st.session_state.current_score * 100)
        sc = "red" if sp > 38 else ("orange" if sp > 22 else "green")
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

    def render_gauge(score, key="gauge"):
        val = score * 100
        if val > 38:
            bc, nc = "#cc0000", "#ff2200"
            steps = [('#001a06',0,22),('#1a0c00',22,38),('#2a0000',38,100)]
        elif val > 22:
            bc, nc = "#cc6600", "#ff8800"
            steps = [('#001a06',0,22),('#1a0c00',22,38),('#1a0000',38,100)]
        else:
            bc, nc = "#00aa44", "#00cc55"
            steps = [('#001a06',0,22),('#0a1a00',22,38),('#180000',38,100)]

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
        gauge_ph.plotly_chart(fig, use_container_width=True, key=key)

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
        colors = ["#cc0000" if s > 38 else "#ff8800" if s > 22 else "#00cc55" for s in scores]

        fig = go.Figure()
        fig.add_hrect(y0=0,  y1=22,  fillcolor="rgba(0,204,85,0.06)",  line_width=0)
        fig.add_hrect(y0=22, y1=38,  fillcolor="rgba(255,136,0,0.06)", line_width=0)
        fig.add_hrect(y0=38, y1=100, fillcolor="rgba(204,0,0,0.07)",   line_width=0)
        fig.add_trace(go.Scatter(
            x=times, y=scores,
            mode='lines+markers',
            line=dict(color='#1e6fff', width=2),
            marker=dict(color=colors, size=7, line=dict(color='#06080f', width=1)),
            fill='tozeroy',
            fillcolor='rgba(30,111,255,0.07)'
        ))
        fig.add_hline(y=22, line=dict(color="rgba(255,136,0,0.3)", width=1, dash="dot"))
        fig.add_hline(y=38, line=dict(color="rgba(204,0,0,0.3)",   width=1, dash="dot"))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=130,
            margin=dict(t=8, b=22, l=30, r=10),
            xaxis=dict(showgrid=False, tickfont=dict(color='#2a3044', size=8),
                       tickangle=-30, color='#2a3044'),
            yaxis=dict(showgrid=False, range=[0,100],
                       tickfont=dict(color='#2a3044', size=8),
                       tickvals=[0,22,38,100], color='#2a3044'),
            showlegend=False
        )
        timeline_ph.markdown(
            '<div class="section-title" style="margin-top:5px;">📈 RISK ESCALATION TIMELINE</div>',
            unsafe_allow_html=True)
        timeline_ph.plotly_chart(fig, use_container_width=True,
                                 key=f"timeline_{len(tl)}")

    render_gauge(0, key="gauge_init")
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

# ── FIX: render_history defined OUTSIDE the `with right_col:` block
#    so it can be called freely without re-entering column context,
#    but history_ph is still the placeholder inside that column. ──
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
            speaker = e.get('speaker', 'attacker')

            if speaker == 'victim':
                cs = e.get('compliance_score', 0.0)
                rt = e.get('response_type', 'neutral')
                if rt == 'resistance':
                    tc, badge = "safe-tag", f"✋ RESISTANT ({round(cs,2)})"
                elif rt == 'info_leak':
                    tc, badge = "danger-tag", f"🚨 INFO LEAKED"
                elif cs > 0.3:
                    tc, badge = "danger-tag", f"⚠ HIGH COMPLIANCE ({round(cs,2)})"
                elif cs > 0.1:
                    tc, badge = "warn-tag", f"⚡ COMPLIANCE ({round(cs,2)})"
                else:
                    tc, badge = "safe-tag", f"✓ NEUTRAL"
                speaker_label = '<span style="color:#00cc55;font-size:0.6rem;">🟢 VICTIM</span>'
            else:
                if e['score'] > 0.38:
                    tc, badge = "danger-tag", f"⚠ HIGH RISK — {sp}%"
                elif e['score'] > 0.22:
                    tc, badge = "warn-tag",   f"⚡ SUSPICIOUS — {sp}%"
                else:
                    tc, badge = "safe-tag",   f"✓ SAFE — {sp}%"
                speaker_label = '<span style="color:#cc0000;font-size:0.6rem;">🔴 ATTACKER</span>'

            # ── FIX: groups may be stored as list or set; handle both ──
            groups_val = e.get("groups", [])
            if isinstance(groups_val, set):
                groups_list = list(groups_val)
            else:
                groups_list = list(groups_val)

            kw_html = (
                f'<div style="font-size:0.62rem;color:#aa0033;margin-top:2px;">'
                f'🔑 {", ".join(groups_list[:4])}</div>'
            ) if groups_list else ""

            combo_html = (
                f'<div style="font-size:0.62rem;color:#cc0044;margin-top:1px;">'
                f'⚡ {e["combo"]}</div>'
            ) if e.get("combo") else ""

            emo_html = ""
            for emo, ecls, eico in e.get('emotions', []):
                emo_html += f'<span class="emotion-badge {ecls}">{eico} {emo}</span>'

            safe_text = e['text'][:150] + ('...' if len(e['text']) > 150 else '')
            html += (
                '<div class="history-entry">'
                f'<div class="history-time">{e["time"]} &nbsp; {speaker_label}</div>'
                f'<div class="history-text">{safe_text}</div>'
                f'{kw_html}{combo_html}{emo_html}'
                f'<div class="{tc}">{badge}</div>'
                '</div>'
            )
        history_ph.markdown(html, unsafe_allow_html=True)

# Always render history on every rerun so it stays up to date
render_history()

# ════════════════════════════════════════════
# HELPER — shared recording + transcription
# ════════════════════════════════════════════
def record_and_transcribe(duration=8, sample_rate=16000):
    audio = sd.rec(int(duration * sample_rate),
                   samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    audio = np.squeeze(audio)

    if audio is None or len(audio) == 0:
        return ""
    if np.max(np.abs(audio)) < 0.001:
        return ""

    audio = audio.astype(np.float32)
    write("temp.wav", sample_rate, audio)

    import gc
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    segments, info = whisper_model.transcribe("temp.wav", beam_size=1, vad_filter=True)
    text = " ".join([segment.text for segment in segments]).strip()

    if not text or len(text.strip()) < 2:
        return None

    return text

def score_attacker_turn(text, chunk_count):
    if is_safe_context(text):
        prev = st.session_state.current_score
        return {
            "score": prev * 0.4, "probability": 0.0,
            "keyword_score": 0.0, "groups_hit": set(),
            "combo_name": None, "emotions": [],
        }

    context_text = get_context_text(text, st.session_state.transcript_window)

    text_vec         = vectorizer.transform([text])
    kw_score_ml, groups_hit_ml, _ = compute_keyword_score(text)
    kw_groups_ml     = len(groups_hit_ml)
    kw_combo_ml      = 1 if kw_score_ml > 0 else 0
    kw_flags         = [
        1 if any(kw in text.lower() for kw in CIALDINI_GROUPS[g]["keywords"]) else 0
        for g in CIALDINI_GROUPS.keys()
    ]
    numeric_features = [kw_score_ml, kw_groups_ml, kw_combo_ml] + kw_flags
    num_vec          = csr_matrix([numeric_features])
    final_input      = hstack([text_vec, num_vec])
    probability      = model.predict_proba(final_input)[0][1]

    if probability < MIN_CONFIDENCE:
        return {
            "score": 0.0, "probability": probability,
            "keyword_score": 0.0, "groups_hit": set(),
            "combo_name": None, "emotions": [],
        }

    keyword_score, groups_hit, combo_name = compute_keyword_score(context_text)

    hits = len(groups_hit)
    if hits >= 2:
        st.session_state.keyword_hit_count += hits
        st.session_state.escalation_bonus = min(
            st.session_state.escalation_bonus + 0.04 * hits, 0.35)
    else:
        st.session_state.escalation_bonus = max(
            st.session_state.escalation_bonus - 0.02, 0.0)

    base_final = min(probability + 0.10 * keyword_score, 1.0)
    raw_score  = min(base_final + st.session_state.escalation_bonus, 1.0)
    prev       = st.session_state.current_score
    new_score  = prev + (raw_score - prev) * (0.8 if raw_score > prev else 0.3)

    return {
        "score": new_score, "probability": probability,
        "keyword_score": keyword_score, "groups_hit": groups_hit,
        "combo_name": combo_name, "emotions": detect_emotions(text),
    }


# ════════════════════════════════════════════
# ATTACKER RECORDING
# ════════════════════════════════════════════
if st.session_state.record_attacker and st.session_state.running:
    st.session_state.record_attacker = False
    chunk_count = st.session_state.total_chunks + 1

    render_mic(True)
    render_soundwave(True)
    status_ph.markdown(
        '<div class="status-listening">🔴 &nbsp; RECORDING ATTACKER...</div>',
        unsafe_allow_html=True)

    text = record_and_transcribe()
    render_soundwave(False)

    if not text:
        render_mic(False)
        status_ph.markdown(
            '<div class="status-safe">🔇 &nbsp; NO SPEECH DETECTED</div>',
            unsafe_allow_html=True)
    else:
        try:
            result = score_attacker_turn(text, chunk_count)
        except Exception as e:
            st.error(f"SCORING ERROR: {e}")
            st.stop()

        new_score     = result["score"]
        probability   = result["probability"]
        keyword_score = result["keyword_score"]
        groups_hit    = result["groups_hit"]
        combo_name    = result["combo_name"]
        emotions      = result["emotions"]

        st.session_state.current_score         = new_score
        st.session_state.total_chunks         += 1
        st.session_state.last_attacker_score   = new_score
        st.session_state.last_attacker_groups  = groups_hit
        if new_score > 0.38:
            st.session_state.high_risk_count += 1

        # ── FIX: store groups as a plain list (JSON-serialisable, renderable) ──
        st.session_state.history.append({
            'time':     datetime.datetime.now().strftime("%H:%M:%S"),
            'text':     text,
            'score':    new_score,
            'ml':       probability,
            'keywords': keyword_score,
            'groups':   list(groups_hit),   # ← was set(); now always list
            'combo':    combo_name,
            'emotions': emotions,
            'speaker':  'attacker',
        })

        st.session_state.conversation.append({
            'speaker': 'attacker',
            'text':    text,
            'score':   new_score,
            'groups':  groups_hit,
            'combo':   combo_name,
            'time':    datetime.datetime.now().strftime("%H:%M:%S"),
        })

        st.session_state.risk_timeline.append((
            datetime.datetime.now().strftime("%H:%M:%S"), new_score))

        render_gauge(new_score, key=f"gauge_{chunk_count}")

        if new_score > 0.38:
            status_ph.markdown(
                '<div class="status-danger">⚠ &nbsp; HIGH FRAUD RISK — ATTACKER</div>',
                unsafe_allow_html=True)
        elif new_score > 0.22:
            status_ph.markdown(
                '<div class="status-warning">⚡ &nbsp; SUSPICIOUS — ATTACKER</div>',
                unsafe_allow_html=True)
        else:
            status_ph.markdown(
                '<div class="status-safe">✓ &nbsp; ATTACKER — LOW RISK</div>',
                unsafe_allow_html=True)

        render_mic(new_score > 0.22)

        if emotions:
            badges = "".join(
                f'<span class="emotion-badge {ecls}">{eico} {emo}</span>'
                for emo, ecls, eico in emotions)
            emotion_ph.markdown(
                f'<div style="margin:3px 0 4px 0;">{badges}</div>',
                unsafe_allow_html=True)
        else:
            emotion_ph.markdown("", unsafe_allow_html=True)

        transcript_ph.markdown(
            '<div class="section-title" style="margin-top:4px;">🔴 ATTACKER — LATEST</div>'
            f'<div class="transcript-box">{text}</div>',
            unsafe_allow_html=True)

        formula_line = (
            f'ML({round(probability,2)}) + 0.10×KW({round(keyword_score,2)})'
            f' + ESC(+{round(st.session_state.escalation_bonus,2)})'
            f' = {round(new_score,2)}  [thresh:0.38]'
        )
        groups_line = ", ".join(sorted(groups_hit)) if groups_hit else "none"
        combo_line  = f'⚡ COMBO: {combo_name}' if combo_name else ""
        detail_ph.markdown(
            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.62rem;'
            f'color:#2a3044;text-align:center;letter-spacing:1px;margin-top:2px;line-height:1.6;">'
            f'{formula_line}<br><span style="color:#1a2a44;">Groups: {groups_line}</span>'
            + (f'<br><span style="color:#cc0044;">{combo_line}</span>' if combo_line else "")
            + '</div>', unsafe_allow_html=True)

        render_metrics()
        render_timeline()
        # ── FIX: call render_history() directly — no `with right_col:` wrapper ──
        render_history()


# ════════════════════════════════════════════
# VICTIM RECORDING
# ════════════════════════════════════════════
if st.session_state.record_victim and st.session_state.running:
    st.session_state.record_victim = False

    render_mic(True)
    render_soundwave(True)
    status_ph.markdown(
        '<div class="status-listening">🟢 &nbsp; RECORDING VICTIM...</div>',
        unsafe_allow_html=True)

    text = record_and_transcribe()
    render_soundwave(False)
    render_mic(False)

    if not text:
        status_ph.markdown(
            '<div class="status-safe">🔇 &nbsp; NO SPEECH DETECTED</div>',
            unsafe_allow_html=True)
    else:
        compliance_score, response_type = score_victim_response(
            text,
            st.session_state.get("last_attacker_groups", set()),
            st.session_state.last_attacker_score
        )

        if compliance_score > 0.15:
            st.session_state.consecutive_compliances += 1
        else:
            st.session_state.consecutive_compliances = 0

        st.session_state.conversation.append({
            'speaker':          'victim',
            'text':             text,
            'score':            0.0,
            'groups':           [],
            'combo':            None,
            'compliance_score': compliance_score,
            'response_type':    response_type,
            'time':             datetime.datetime.now().strftime("%H:%M:%S"),
        })

        st.session_state.history.append({
            'time':             datetime.datetime.now().strftime("%H:%M:%S"),
            'text':             text,
            'score':            0.0,
            'ml':               0.0,
            'keywords':         0.0,
            'groups':           [],          # ← consistent: always list
            'combo':            None,
            'emotions':         [],
            'speaker':          'victim',
            'compliance_score': compliance_score,
            'response_type':    response_type,
        })

        if response_type == "resistance":
            c_color = "#00cc55"
            c_label = f"✋ RESISTANT ({round(compliance_score,2)})"
        elif response_type == "info_leak":
            c_color = "#cc0000"
            c_label = f"🚨 INFO LEAKED ({round(compliance_score,2)})"
        elif compliance_score > 0.3:
            c_color = "#cc0000"
            c_label = f"⚠ HIGH COMPLIANCE ({round(compliance_score,2)})"
        elif compliance_score > 0.1:
            c_color = "#ff8800"
            c_label = f"⚡ PARTIAL COMPLIANCE ({round(compliance_score,2)})"
        else:
            c_color = "#00cc55"
            c_label = f"✓ NEUTRAL ({round(compliance_score,2)})"

        transcript_ph.markdown(
            '<div class="section-title" style="margin-top:4px;">🟢 VICTIM — RESPONSE</div>'
            f'<div class="transcript-box">{text}</div>',
            unsafe_allow_html=True)

        detail_ph.markdown(
            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.72rem;'
            f'color:{c_color};text-align:center;letter-spacing:1px;margin-top:4px;">'
            f'VICTIM COMPLIANCE: {c_label}<br>'
            f'<span style="color:#2a3044;font-size:0.6rem;">'
            f'Response Type: {response_type} | '
            f'Consecutive Compliances: {st.session_state.consecutive_compliances}'
            f'</span></div>',
            unsafe_allow_html=True)

        # ── FIX: call render_history() directly ──
        render_history()


# ════════════════════════════════════════════
# FINAL ANALYSIS PANEL
# ════════════════════════════════════════════
if st.session_state.final_analysis_done and st.session_state.final_result:
    r = st.session_state.final_result
    is_ml = "combined_score" in r
    score  = r.get("combined_score", r.get("final_score", 0.0))
    color  = r["color"]
    is_fallback = r.get("_fallback", False)

    st.markdown("---")
    bd = r.get("breakdown", {})

    title_text = ("DUAL-LAYER ML CONVERSATION ANALYSIS"
                  if (is_ml and not is_fallback)
                  else "CONVERSATION ANALYSIS (RULE-BASED FALLBACK)")

    layer_blocks = ""
    if is_ml and not is_fallback:
        layer_blocks = (
            f'<div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;margin-bottom:12px;">'
            f'<div style="background:#06080f;border:1px solid #1a2030;border-radius:6px;padding:8px 14px;min-width:110px;">'
            f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;">LAYER 1</div>'
            f'<div style="font-size:0.55rem;color:#2a3044;margin-bottom:4px;">SENTENCE ML AVG</div>'
            f'<div style="font-size:1.1rem;color:#1e6fff;">{int(r["ml1_avg_score"]*100)}%</div></div>'
            f'<div style="background:#06080f;border:1px solid #1a2030;border-radius:6px;padding:8px 14px;min-width:110px;">'
            f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;">LAYER 2</div>'
            f'<div style="font-size:0.55rem;color:#2a3044;margin-bottom:4px;">CONVERSATION ML</div>'
            f'<div style="font-size:1.1rem;color:#cc0000;">{int(r["ml2_score"]*100)}%</div></div>'
            f'<div style="background:#06080f;border:1px solid #1a2030;border-radius:6px;padding:8px 14px;min-width:110px;">'
            f'<div style="font-size:0.55rem;color:#2a3044;letter-spacing:2px;">ENSEMBLE</div>'
            f'<div style="font-size:0.55rem;color:#2a3044;margin-bottom:4px;">0.55xL2 + 0.45xL1</div>'
            f'<div style="font-size:1.1rem;color:{color};">{int(score*100)}%</div></div>'
            f'</div>'
        )

    info_block = ""
    if r.get("info_disclosed"):
        info_block = (
            f'<div style="color:#cc0000;font-size:0.8rem;font-weight:bold;'
            f'border:1px solid #cc0000;border-radius:4px;padding:6px;margin-top:6px;">'
            f'CRITICAL: PERSONAL INFORMATION WAS DISCLOSED</div>'
        )

    comp_val = round(r.get("avg_compliance", bd.get("compliance_avg", 0.0)), 2)
    res_val  = r.get("resistance_count", 0)
    pri_val  = r.get("num_principles", 0)
    str_val  = bd.get("max_compliance_streak", 0)
    dom_str  = ", ".join(r.get("dominant_principles", [])) or "none"
    atk_t    = bd.get("attacker_turns", r.get("attacker_turns", "?"))
    vic_t    = bd.get("victim_turns",   r.get("victim_turns",   "?"))

    st.markdown(
        f'<div style="font-family:Share Tech Mono,monospace;text-align:center;'
        f'padding:22px;background:#0b0e1a;border:2px solid {color};'
        f'border-radius:10px;margin-top:10px;">'
        f'<div style="font-size:0.65rem;color:#2a3044;letter-spacing:3px;margin-bottom:8px;">{title_text}</div>'
        f'<div style="font-size:2.2rem;color:{color};text-shadow:0 0 24px {color}55;font-weight:bold;">{int(score*100)}%</div>'
        f'<div style="font-size:0.95rem;color:{color};letter-spacing:2px;margin:6px 0 14px 0;">{r["verdict"]}</div>'
        f'{layer_blocks}'
        f'<div style="display:flex;justify-content:center;gap:18px;flex-wrap:wrap;font-size:0.62rem;color:#2a3044;margin-bottom:10px;">'
        f'<span>COMPLIANCE: <span style="color:#ff8800">{comp_val}</span></span>'
        f'<span>RESISTANCE: <span style="color:#00cc55">{res_val}</span></span>'
        f'<span>PRINCIPLES: <span style="color:#1e6fff">{pri_val}</span></span>'
        f'<span>STREAK: <span style="color:#ff8800">{str_val}</span></span>'
        f'</div>'
        f'<div style="font-size:0.62rem;color:#2a3044;margin-bottom:8px;">'
        f'Dominant principles: <span style="color:#1e6fff">{dom_str}</span>'
        f' &nbsp;|&nbsp; Turns: <span style="color:#cc0000">{atk_t}</span> attacker / '
        f'<span style="color:#00cc55">{vic_t}</span> victim</div>'
        f'{info_block}</div>',
        unsafe_allow_html=True
    )