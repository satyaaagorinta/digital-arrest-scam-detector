# import joblib

# # Load saved model
# model = joblib.load("models/scam_model.pkl")
# vectorizer = joblib.load("models/vectorizer.pkl")

# print("Scam Detection Ready!")

# while True:
#     user_input = input("\nEnter message (or type 'exit'): ")

#     if user_input.lower() == 'exit':
#         break

#     # Convert text to vector
#     text_vec = vectorizer.transform([user_input])

#     # Predict
#     prediction = model.predict(text_vec)[0]
#     probability = model.predict_proba(text_vec)[0][1]

#     if prediction == 1:
#         print("⚠️ Scam detected!")
#     else:
#         print("✅ Looks normal")

#     print("Scam Probability:", round(probability, 2))

import joblib
from scipy.sparse import hstack, csr_matrix

# ================================
# CIALDINI KEYWORD GROUPS
# ================================

CIALDINI_GROUPS = {
    "authority": {
        "score": 0.30,
        "keywords": [
            "cbi officer", "cyber crime department", "enforcement directorate",
            "income tax officer", "trai officer", "rbi officer", "narcotics",
            "anti terrorism squad", "national investigation agency",
            "financial intelligence unit", "economic offences wing",
            "serious fraud investigation office", "sebi officer",
            "ministry of home affairs", "supreme court", "high court",
            "sessions court", "magistrate", "central vigilance commission",
            "inspector general", "deputy commissioner", "superintendent of police",
            "cid officer", "joint director", "directorate of revenue intelligence",
            "sfio", "lokayukta", "lokpal", "cert-in", "intelligence bureau",
            "national crime records bureau", "interpol", "ed officer",
            "anti corruption bureau", "election commission", "dcp",
            "nia officer", "crime branch", "vigilance officer", "police officer",
            "government officer", "court appointed", "judicial officer",
            "senior officer", "investigation officer", "cyber cell",
            "national cyber crime", "ncpcr", "treasury officer",
            "jaanch adhikaari", "sarkaari adhikaari", "vibhaag se",
            "cbi se hain", "police vibhaag", "court ka order",
        ]
    },

    # G2 — URGENCY / SCARCITY OF TIME (score 0.30)
    # Creates artificial time pressure to prevent rational thinking
    "urgency": {
        "score": 0.30,
        "keywords": [
            "within 24 hours", "immediately", "right now", "last chance",
            "final notice", "last warning", "within 2 hours", "60 minutes",
            "30 minutes", "45 minutes", "tonight", "today only",
            "no time left", "before midnight", "by end of day",
            "abhi", "turant", "abhi ke abhi", "24 ghante mein",
            "ek ghante mein", "2 ghante mein", "aaj raat tak",
            "aaj tak", "jaldi karo", "der mat karo", "aakhri mauka",
            "last date", "deadline", "no more time", "running out of time",
            "act now", "do not delay", "final opportunity", "last moment",
        ]
    },

    # G3 — SCARCITY (score 0.25)
    # Implies the offer to resolve is rare or expiring
    "scarcity": {
        "score": 0.25,
        "keywords": [
            "one time settlement", "one time waiver", "limited time offer",
            "only chance", "cannot be extended", "no second chance",
            "this offer expires", "once in a lifetime", "rare opportunity",
            "special window", "last opportunity", "after this call",
            "ek baar ka mauka", "yeh mauka nahi milega", "aakhri baar",
            "ab nahi hoga", "sirf aaj", "only today", "out of court settle",
            "settlement window", "government scheme aaj tak",
            "after today no help", "cannot help after this",
        ]
    },

    # G4 — WARRANT / LEGAL THREAT (score 0.25)
    # Uses threat of legal process to intimidate
    "warrant": {
        "score": 0.25,
        "keywords": [
            "arrest warrant", "non-bailable warrant", "look-out notice",
            "court order", "fir registered", "fir darj", "legal notice",
            "summons", "court summons", "attachment order", "seizure order",
            "warrant execute", "warrant issued", "bailable warrant",
            "anticipatory bail", "preventive detention", "section 420",
            "pmla", "fema violation", "ipc section", "contempt of court",
            "sub judice", "ex-parte order", "charge sheet", "bail rejected",
            "giraftaari ka warrant", "court notice", "girtaari ka aadesh",
            "non bailable", "warrant aayega", "notice aayega",
        ]
    },

    # G5 — MONEY / FINANCIAL COERCION (score 0.30)
    # Demands financial payment to resolve fake threat
    "money": {
        "score": 0.30,
        "keywords": [
            "transfer money", "send money", "pay immediately", "transfer funds",
            "wire transfer", "pay fine", "security deposit", "processing fee",
            "verification fee", "settlement amount", "clearance fee",
            "pay the penalty", "pay or face", "deposit amount",
            "escrow account", "secret account", "government account",
            "paise transfer karo", "abhi paise bhejo", "turant transfer",
            "fine bharo", "fees bharo", "payment karo", "jama karo",
            "amount bhejo", "rupees transfer", "lakh transfer",
            "hawala payment", "cash deposit", "online payment karo",
            "neft karo", "rtgs karo", "upi se bhejo",
        ]
    },

    # G6 — RECIPROCITY (score 0.20)
    # Pretends to help/protect the victim to create obligation
    "reciprocity": {
        "score": 0.20,
        "keywords": [
            "we are trying to help you", "we want to protect you",
            "i am on your side", "we are your well-wishers",
            "helping you out", "doing you a favour", "personally ensuring",
            "i will personally", "guarantee your safety", "protect your family",
            "immunity from prosecution", "clean chit guarantee",
            "case close karenge", "aapko bachayenge", "aapki help kar rahe hain",
            "aapke saath hain", "aapka bhala chahte hain",
            "personally handle karunga", "sifarish karenge",
            "leniency dilaayenge", "aapko protect karenge",
            "hum guarantee dete hain", "aapke liye kuch kar sakte hain",
        ]
    },

    # G7 — THREAT / FEAR (score 0.30)
    # Direct threats to person, family, property, reputation
    "threat": {
        "score": 0.30,
        "keywords": [
            "face arrest", "you will be arrested", "arrested tonight",
            "jail bheja jayega", "prison mein jaoge", "aapko pakad lenge",
            "raid padegi", "police aayegi", "officer aa raha hai",
            "property seized", "assets frozen", "account blocked",
            "media mein aayega", "employer ko batayenge", "family ko involve",
            "aapki beti arrested", "aapka beta case mein", "family member named",
            "reputation destroy", "public embarrassment", "nationwide notice",
            "travel ban", "passport blacklisted", "criminal record",
            "dhamki", "khatre mein", "consequences severe",
            "will not be able to help", "cannot save you after this",
        ]
    },

    # G8 — ACCOUNT / IDENTITY (score 0.20)
    # Targets bank/identity credentials to enable fraud
    "account": {
        "score": 0.20,
        "keywords": [
            "share your otp", "otp batao", "account number share",
            "net banking credentials", "atm card number", "cvv number",
            "pin number", "share bank details", "verify account",
            "aadhaar number share", "pan number verify", "account verification",
            "kyc update", "kyc verify karo", "biometric verify",
            "screen share karo", "remote access", "aadhar otp share",
            "netbanking username", "password share", "login details",
            "account details share", "banking details", "debit card details",
            "credit card number", "ifsc share", "account froze",
            "account suspend", "aapka account block", "frozen account",
        ]
    },

    # G9 — DISTRACTION / CONFUSION (score 0.25)
    # Overwhelming victim with official-sounding jargon
    "distraction": {
        "score": 0.25,
        "keywords": [
            "sealed case", "confidential investigation", "classified matter",
            "national security", "media blackout", "nda sign karo",
            "do not tell anyone", "kisi ko mat batao", "keep this confidential",
            "do not contact lawyer", "do not inform family",
            "this is a secret operation", "sub judice matter",
            "sensitive case", "high profile matter", "sealed envelope",
            "case number", "ticket number", "reference number generated",
            "stay on the line", "do not hang up", "do not disconnect",
            "aap monitored hain", "call record ho rahi hai",
            "yeh recorded call hai", "evidence ke roop mein",
        ]
    },

    # G10 — SOCIAL PROOF (score 0.20)
    # Uses fake evidence of others to validate claims
    "social_proof": {
        "score": 0.20,
        "keywords": [
            "multiple complaints against you", "47 complaints",
            "23 complaints", "witnesses against you", "3 witnesses",
            "your neighbor reported", "your employee reported",
            "your business partner named you", "your friend is a witness",
            "your family member named", "anonymous complaint",
            "whistleblower aayi hai", "gawah hain aapke khilaf",
            "3 independent witnesses", "complaints received",
            "national portal par complaints", "public complaints",
        ]
    },

    # G11 — COMMITMENT / CONSISTENCY (score 0.20)
    # Locks victim into cooperation incrementally
    "commitment": {
        "score": 0.20,
        "keywords": [
            "you already agreed", "you said you would cooperate",
            "you confirmed earlier", "stay on call", "remain on line",
            "do not move from location", "you have acknowledged",
            "legal obligation", "legally bound", "mandatory compliance",
            "you must cooperate", "aap agree kar chuke hain",
            "aapko cooperate karna hoga", "aap legally bound hain",
            "aapko comply karna hoga", "aap pe legal obligation hai",
            "undertaking sign karni hogi", "affidavit deni hogi",
            "you are obligated", "cooperation mandatory",
        ]
    },
}

COMBINATIONS = [
    # Most dangerous — full psychological trap
    {
        "name": "commitment + reciprocity + consistency",
        "groups": ["commitment", "reciprocity", "distraction"],
        "bonus": 0.35,
        "desc": "Victim is locked in, feels obligated, and confused"
    },
    {
        "name": "authority + urgency + threat",
        "groups": ["authority", "urgency", "threat"],
        "bonus": 0.40,
        "desc": "Classic digital arrest pattern — most common"
    },
    {
        "name": "authority + money + commitment",
        "groups": ["authority", "money", "commitment"],
        "bonus": 0.35,
        "desc": "Pay-or-arrested pattern with official cover"
    },
    {
        "name": "authority + warrant + urgency",
        "groups": ["authority", "warrant", "urgency"],
        "bonus": 0.38,
        "desc": "Legal threat with time pressure from fake official"
    },
    {
        "name": "threat + money + scarcity",
        "groups": ["threat", "money", "scarcity"],
        "bonus": 0.33,
        "desc": "Pay now or lose your only chance — coercion loop"
    },
    {
        "name": "distraction + account + authority",
        "groups": ["distraction", "account", "authority"],
        "bonus": 0.30,
        "desc": "Credential phishing under official pretense"
    },
    {
        "name": "social_proof + authority + threat",
        "groups": ["social_proof", "authority", "threat"],
        "bonus": 0.28,
        "desc": "Many complaints plus official plus threat"
    },
    {
        "name": "reciprocity + commitment + money",
        "groups": ["reciprocity", "commitment", "money"],
        "bonus": 0.28,
        "desc": "We're helping you, you agreed, now pay"
    },
    {
        "name": "urgency + scarcity + money",
        "groups": ["urgency", "scarcity", "money"],
        "bonus": 0.25,
        "desc": "Last chance to pay before offer disappears"
    },
    {
        "name": "distraction + warrant + commitment",
        "groups": ["distraction", "warrant", "commitment"],
        "bonus": 0.25,
        "desc": "Sealed case, warrant, you must comply"
    },
    # Two-group dangerous combos
    {
        "name": "authority + urgency",
        "groups": ["authority", "urgency"],
        "bonus": 0.20,
        "desc": "Official + time pressure"
    },
    {
        "name": "authority + money",
        "groups": ["authority", "money"],
        "bonus": 0.20,
        "desc": "Official demanding payment"
    },
    {
        "name": "threat + urgency",
        "groups": ["threat", "urgency"],
        "bonus": 0.20,
        "desc": "Arrest threat with time deadline"
    },
    {
        "name": "account + urgency",
        "groups": ["account", "urgency"],
        "bonus": 0.18,
        "desc": "Credential grab with time pressure"
    },
    {
        "name": "distraction + money",
        "groups": ["distraction", "money"],
        "bonus": 0.15,
        "desc": "Confidential + pay"
    },
]

# ================================
# KEYWORD SCORE FUNCTION
# ================================

def compute_keyword_score(text):
    text = text.lower()
    groups_hit = set()
    base_score = 0.0

    for group_name, group_data in CIALDINI_GROUPS.items():
        for kw in group_data["keywords"]:
            if kw in text:
                if group_name not in groups_hit:
                    base_score += group_data["score"]
                    groups_hit.add(group_name)
                break

    combo_bonus = 0.0
    for combo in COMBINATIONS:
        if set(combo["groups"]).issubset(groups_hit):
            combo_bonus = max(combo_bonus, combo["bonus"])

    keyword_score = min(base_score + combo_bonus, 1.0)
    return keyword_score, groups_hit, combo_bonus


# ================================
# LOAD MODEL
# ================================

model = joblib.load("models/scam_model.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

print("🚀 Scam Detection Ready!")

# ================================
# PREDICTION LOOP
# ================================

while True:
    user_input = input("\nEnter message (or type 'exit'): ")

    if user_input.lower() == 'exit':
        break

    # -------- TF-IDF --------
    text_vec = vectorizer.transform([user_input])

    # -------- KEYWORD FEATURES --------
    kw_score, groups_hit, combo = compute_keyword_score(user_input)

    kw_groups = len(groups_hit)
    kw_combo = 1 if combo else 0

    kw_flags = []
    for group_name in CIALDINI_GROUPS.keys():
        flag = 1 if any(
            kw in user_input.lower()
            for kw in CIALDINI_GROUPS[group_name]['keywords']
        ) else 0
        kw_flags.append(flag)

    numeric_features = [kw_score, kw_groups, kw_combo] + kw_flags
    num_vec = csr_matrix([numeric_features])

    # -------- COMBINE --------
    final_input = hstack([text_vec, num_vec])

    # DEBUG (optional)
    # print(final_input.shape)  # should be (1, 12931)

    # -------- PREDICT --------
    prediction = model.predict(final_input)[0]
    probability = model.predict_proba(final_input)[0][1]

    if prediction == 1:
        print("⚠️ Scam detected!")
    else:
        print("✅ Looks normal")

    print("Scam Probability:", round(probability, 2))