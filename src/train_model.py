

# """
# train_model.py — Scam Shield Training Pipeline
# Incorporates:
#   - Cialdini's 11 Principles of Persuasion keyword groups
#   - Combination detection from "Principles of Persuasion in Social Engineering"
#   - 80/20 train/test split
#   - Keyword score capped at 1.0
#   - Final score = 0.7 * ML_score + 0.3 * keyword_score
# """

# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.linear_model import LogisticRegression
# from sklearn.metrics import (accuracy_score, classification_report,
#                               confusion_matrix, roc_auc_score)
# from sklearn.pipeline import Pipeline
# import joblib
# import json
# import os

# # ─────────────────────────────────────────────
# # 1. LOAD & MERGE DATASETS
# # ─────────────────────────────────────────────
# print("Loading dataset...")

# df = pd.read_csv("data/digital_arrest_dataset.csv")
# df = df[['text', 'label']].dropna()
# df['label'] = df['label'].astype(int)
# df['text']  = df['text'].astype(str).str.strip()
# df = df[df['text'].str.len() > 5]

# print(f"Total samples: {len(df)}")
# print(f"  Scam (1):   {(df['label'] == 1).sum()}")
# print(f"  Normal (0): {(df['label'] == 0).sum()}")

# # ─────────────────────────────────────────────
# # 2. CIALDINI KEYWORD GROUPS
# #    Source: Cialdini (1984) "Influence: The Psychology of Persuasion"
# #    + Workman (2008) "Situational social influence and human behavior"
# #    + Gragg (2003) "Phishing" SANS Institute
# # ─────────────────────────────────────────────

# CIALDINI_GROUPS = {

#     # G1 — AUTHORITY (score 0.30)
#     # Exploits deference to legitimate-sounding officials
#     "authority": {
#         "score": 0.30,
#         "keywords": [
#             "cbi officer", "cyber crime department", "enforcement directorate",
#             "income tax officer", "trai officer", "rbi officer", "narcotics",
#             "anti terrorism squad", "national investigation agency",
#             "financial intelligence unit", "economic offences wing",
#             "serious fraud investigation office", "sebi officer",
#             "ministry of home affairs", "supreme court", "high court",
#             "sessions court", "magistrate", "central vigilance commission",
#             "inspector general", "deputy commissioner", "superintendent of police",
#             "cid officer", "joint director", "directorate of revenue intelligence",
#             "sfio", "lokayukta", "lokpal", "cert-in", "intelligence bureau",
#             "national crime records bureau", "interpol", "ed officer",
#             "anti corruption bureau", "election commission", "dcp",
#             "nia officer", "crime branch", "vigilance officer", "police officer",
#             "government officer", "court appointed", "judicial officer",
#             "senior officer", "investigation officer", "cyber cell",
#             "national cyber crime", "ncpcr", "treasury officer",
#             "jaanch adhikaari", "sarkaari adhikaari", "vibhaag se",
#             "cbi se hain", "police vibhaag", "court ka order",
#         ]
#     },

#     # G2 — URGENCY / SCARCITY OF TIME (score 0.30)
#     # Creates artificial time pressure to prevent rational thinking
#     "urgency": {
#         "score": 0.30,
#         "keywords": [
#             "within 24 hours", "immediately", "right now", "last chance",
#             "final notice", "last warning", "within 2 hours", "60 minutes",
#             "30 minutes", "45 minutes", "tonight", "today only",
#             "no time left", "before midnight", "by end of day",
#             "abhi", "turant", "abhi ke abhi", "24 ghante mein",
#             "ek ghante mein", "2 ghante mein", "aaj raat tak",
#             "aaj tak", "jaldi karo", "der mat karo", "aakhri mauka",
#             "last date", "deadline", "no more time", "running out of time",
#             "act now", "do not delay", "final opportunity", "last moment",
#         ]
#     },

#     # G3 — SCARCITY (score 0.25)
#     # Implies the offer to resolve is rare or expiring
#     "scarcity": {
#         "score": 0.25,
#         "keywords": [
#             "one time settlement", "one time waiver", "limited time offer",
#             "only chance", "cannot be extended", "no second chance",
#             "this offer expires", "once in a lifetime", "rare opportunity",
#             "special window", "last opportunity", "after this call",
#             "ek baar ka mauka", "yeh mauka nahi milega", "aakhri baar",
#             "ab nahi hoga", "sirf aaj", "only today", "out of court settle",
#             "settlement window", "government scheme aaj tak",
#             "after today no help", "cannot help after this",
#         ]
#     },

#     # G4 — WARRANT / LEGAL THREAT (score 0.25)
#     # Uses threat of legal process to intimidate
#     "warrant": {
#         "score": 0.25,
#         "keywords": [
#             "arrest warrant", "non-bailable warrant", "look-out notice",
#             "court order", "fir registered", "fir darj", "legal notice",
#             "summons", "court summons", "attachment order", "seizure order",
#             "warrant execute", "warrant issued", "bailable warrant",
#             "anticipatory bail", "preventive detention", "section 420",
#             "pmla", "fema violation", "ipc section", "contempt of court",
#             "sub judice", "ex-parte order", "charge sheet", "bail rejected",
#             "giraftaari ka warrant", "court notice", "girtaari ka aadesh",
#             "non bailable", "warrant aayega", "notice aayega",
#         ]
#     },

#     # G5 — MONEY / FINANCIAL COERCION (score 0.30)
#     # Demands financial payment to resolve fake threat
#     "money": {
#         "score": 0.30,
#         "keywords": [
#             "transfer money", "send money", "pay immediately", "transfer funds",
#             "wire transfer", "pay fine", "security deposit", "processing fee",
#             "verification fee", "settlement amount", "clearance fee",
#             "pay the penalty", "pay or face", "deposit amount",
#             "escrow account", "secret account", "government account",
#             "paise transfer karo", "abhi paise bhejo", "turant transfer",
#             "fine bharo", "fees bharo", "payment karo", "jama karo",
#             "amount bhejo", "rupees transfer", "lakh transfer",
#             "hawala payment", "cash deposit", "online payment karo",
#             "neft karo", "rtgs karo", "upi se bhejo",
#         ]
#     },

#     # G6 — RECIPROCITY (score 0.20)
#     # Pretends to help/protect the victim to create obligation
#     "reciprocity": {
#         "score": 0.20,
#         "keywords": [
#             "we are trying to help you", "we want to protect you",
#             "i am on your side", "we are your well-wishers",
#             "helping you out", "doing you a favour", "personally ensuring",
#             "i will personally", "guarantee your safety", "protect your family",
#             "immunity from prosecution", "clean chit guarantee",
#             "case close karenge", "aapko bachayenge", "aapki help kar rahe hain",
#             "aapke saath hain", "aapka bhala chahte hain",
#             "personally handle karunga", "sifarish karenge",
#             "leniency dilaayenge", "aapko protect karenge",
#             "hum guarantee dete hain", "aapke liye kuch kar sakte hain",
#         ]
#     },

#     # G7 — THREAT / FEAR (score 0.30)
#     # Direct threats to person, family, property, reputation
#     "threat": {
#         "score": 0.30,
#         "keywords": [
#             "face arrest", "you will be arrested", "arrested tonight",
#             "jail bheja jayega", "prison mein jaoge", "aapko pakad lenge",
#             "raid padegi", "police aayegi", "officer aa raha hai",
#             "property seized", "assets frozen", "account blocked",
#             "media mein aayega", "employer ko batayenge", "family ko involve",
#             "aapki beti arrested", "aapka beta case mein", "family member named",
#             "reputation destroy", "public embarrassment", "nationwide notice",
#             "travel ban", "passport blacklisted", "criminal record",
#             "dhamki", "khatre mein", "consequences severe",
#             "will not be able to help", "cannot save you after this",
#         ]
#     },

#     # G8 — ACCOUNT / IDENTITY (score 0.20)
#     # Targets bank/identity credentials to enable fraud
#     "account": {
#         "score": 0.20,
#         "keywords": [
#             "share your otp", "otp batao", "account number share",
#             "net banking credentials", "atm card number", "cvv number",
#             "pin number", "share bank details", "verify account",
#             "aadhaar number share", "pan number verify", "account verification",
#             "kyc update", "kyc verify karo", "biometric verify",
#             "screen share karo", "remote access", "aadhar otp share",
#             "netbanking username", "password share", "login details",
#             "account details share", "banking details", "debit card details",
#             "credit card number", "ifsc share", "account froze",
#             "account suspend", "aapka account block", "frozen account",
#         ]
#     },

#     # G9 — DISTRACTION / CONFUSION (score 0.25)
#     # Overwhelming victim with official-sounding jargon
#     "distraction": {
#         "score": 0.25,
#         "keywords": [
#             "sealed case", "confidential investigation", "classified matter",
#             "national security", "media blackout", "nda sign karo",
#             "do not tell anyone", "kisi ko mat batao", "keep this confidential",
#             "do not contact lawyer", "do not inform family",
#             "this is a secret operation", "sub judice matter",
#             "sensitive case", "high profile matter", "sealed envelope",
#             "case number", "ticket number", "reference number generated",
#             "stay on the line", "do not hang up", "do not disconnect",
#             "aap monitored hain", "call record ho rahi hai",
#             "yeh recorded call hai", "evidence ke roop mein",
#         ]
#     },

#     # G10 — SOCIAL PROOF (score 0.20)
#     # Uses fake evidence of others to validate claims
#     "social_proof": {
#         "score": 0.20,
#         "keywords": [
#             "multiple complaints against you", "47 complaints",
#             "23 complaints", "witnesses against you", "3 witnesses",
#             "your neighbor reported", "your employee reported",
#             "your business partner named you", "your friend is a witness",
#             "your family member named", "anonymous complaint",
#             "whistleblower aayi hai", "gawah hain aapke khilaf",
#             "3 independent witnesses", "complaints received",
#             "national portal par complaints", "public complaints",
#         ]
#     },

#     # G11 — COMMITMENT / CONSISTENCY (score 0.20)
#     # Locks victim into cooperation incrementally
#     "commitment": {
#         "score": 0.20,
#         "keywords": [
#             "you already agreed", "you said you would cooperate",
#             "you confirmed earlier", "stay on call", "remain on line",
#             "do not move from location", "you have acknowledged",
#             "legal obligation", "legally bound", "mandatory compliance",
#             "you must cooperate", "aap agree kar chuke hain",
#             "aapko cooperate karna hoga", "aap legally bound hain",
#             "aapko comply karna hoga", "aap pe legal obligation hai",
#             "undertaking sign karni hogi", "affidavit deni hogi",
#             "you are obligated", "cooperation mandatory",
#         ]
#     },
# }

# # ─────────────────────────────────────────────
# # 3. COMBINATION SCORES
# #    Based on: "Principles of Persuasion in Social Engineering
# #    and Their Use in Phishing" — Ferreira et al. (2015)
# #    Descending order of danger
# # ─────────────────────────────────────────────

# COMBINATIONS = [
#     # Most dangerous — full psychological trap
#     {
#         "name": "commitment + reciprocity + consistency",
#         "groups": ["commitment", "reciprocity", "distraction"],
#         "bonus": 0.35,
#         "desc": "Victim is locked in, feels obligated, and confused"
#     },
#     {
#         "name": "authority + urgency + threat",
#         "groups": ["authority", "urgency", "threat"],
#         "bonus": 0.40,
#         "desc": "Classic digital arrest pattern — most common"
#     },
#     {
#         "name": "authority + money + commitment",
#         "groups": ["authority", "money", "commitment"],
#         "bonus": 0.35,
#         "desc": "Pay-or-arrested pattern with official cover"
#     },
#     {
#         "name": "authority + warrant + urgency",
#         "groups": ["authority", "warrant", "urgency"],
#         "bonus": 0.38,
#         "desc": "Legal threat with time pressure from fake official"
#     },
#     {
#         "name": "threat + money + scarcity",
#         "groups": ["threat", "money", "scarcity"],
#         "bonus": 0.33,
#         "desc": "Pay now or lose your only chance — coercion loop"
#     },
#     {
#         "name": "distraction + account + authority",
#         "groups": ["distraction", "account", "authority"],
#         "bonus": 0.30,
#         "desc": "Credential phishing under official pretense"
#     },
#     {
#         "name": "social_proof + authority + threat",
#         "groups": ["social_proof", "authority", "threat"],
#         "bonus": 0.28,
#         "desc": "Many complaints plus official plus threat"
#     },
#     {
#         "name": "reciprocity + commitment + money",
#         "groups": ["reciprocity", "commitment", "money"],
#         "bonus": 0.28,
#         "desc": "We're helping you, you agreed, now pay"
#     },
#     {
#         "name": "urgency + scarcity + money",
#         "groups": ["urgency", "scarcity", "money"],
#         "bonus": 0.25,
#         "desc": "Last chance to pay before offer disappears"
#     },
#     {
#         "name": "distraction + warrant + commitment",
#         "groups": ["distraction", "warrant", "commitment"],
#         "bonus": 0.25,
#         "desc": "Sealed case, warrant, you must comply"
#     },
#     # Two-group dangerous combos
#     {
#         "name": "authority + urgency",
#         "groups": ["authority", "urgency"],
#         "bonus": 0.20,
#         "desc": "Official + time pressure"
#     },
#     {
#         "name": "authority + money",
#         "groups": ["authority", "money"],
#         "bonus": 0.20,
#         "desc": "Official demanding payment"
#     },
#     {
#         "name": "threat + urgency",
#         "groups": ["threat", "urgency"],
#         "bonus": 0.20,
#         "desc": "Arrest threat with time deadline"
#     },
#     {
#         "name": "account + urgency",
#         "groups": ["account", "urgency"],
#         "bonus": 0.18,
#         "desc": "Credential grab with time pressure"
#     },
#     {
#         "name": "distraction + money",
#         "groups": ["distraction", "money"],
#         "bonus": 0.15,
#         "desc": "Confidential + pay"
#     },
# ]


# def compute_keyword_score(text):
#     """
#     Compute keyword score based on Cialdini groups + combination bonuses.
#     Returns:
#       - keyword_score (float, capped at 1.0)
#       - groups_hit (set of group names detected)
#       - combination_hit (str or None)
#     """
#     text_lower = text.lower()
#     groups_hit = set()
#     base_score = 0.0

#     for group_name, group_data in CIALDINI_GROUPS.items():
#         for kw in group_data["keywords"]:
#             if kw in text_lower:
#                 # Only count each group once for base score
#                 if group_name not in groups_hit:
#                     base_score += group_data["score"]
#                     groups_hit.add(group_name)
#                 break  # one hit per group is enough

#     # Check combinations
#     combination_bonus = 0.0
#     combination_hit = None
#     for combo in COMBINATIONS:
#         required = set(combo["groups"])
#         if required.issubset(groups_hit):
#             combination_bonus = max(combination_bonus, combo["bonus"])
#             if combination_bonus == combo["bonus"]:
#                 combination_hit = combo["name"]

#     raw = base_score + combination_bonus
#     # Cap at 1.0
#     keyword_score = min(raw, 1.0)
#     return keyword_score, groups_hit, combination_hit


# def final_score(ml_prob, keyword_score):
#     """
#     Keyword is a BOOSTER only — never reduces ML score.
#     final = min(ml_prob + 0.15 * keyword_score, 1.0)
#     Keywords push borderline cases over threshold; cannot pull high-ML scores down.
#     """
#     boost = 0.15 * keyword_score
#     return min(ml_prob + boost, 1.0)


# # ─────────────────────────────────────────────
# # 4. FEATURE ENGINEERING
# # ─────────────────────────────────────────────

# def add_keyword_features(df):
#     """Add keyword group hit flags as additional features for training."""
#     results = df['text'].apply(lambda t: compute_keyword_score(str(t)))
#     df['kw_score']    = results.apply(lambda x: x[0])
#     df['kw_groups']   = results.apply(lambda x: len(x[1]))   # count of groups hit
#     df['kw_combo']    = results.apply(lambda x: 1 if x[2] else 0)  # combo detected?

#     # Individual group flags
#     for group_name in CIALDINI_GROUPS.keys():
#         df[f'kw_{group_name}'] = df['text'].apply(
#             lambda t: 1 if any(
#                 kw in t.lower()
#                 for kw in CIALDINI_GROUPS[group_name]['keywords']
#             ) else 0
#         )
#     return df

# print("Computing keyword features...")
# df = add_keyword_features(df)

# # ─────────────────────────────────────────────
# # 5. TRAIN / TEST SPLIT — 80 / 20
# # ─────────────────────────────────────────────

# X_text = df['text']
# y      = df['label']

# # Additional numeric features
# numeric_cols = ['kw_score', 'kw_groups', 'kw_combo'] + \
#                [f'kw_{g}' for g in CIALDINI_GROUPS.keys()]
# X_numeric = df[numeric_cols]

# X_text_train, X_text_test, \
# X_num_train,  X_num_test,  \
# y_train,      y_test = train_test_split(
#     X_text, X_numeric, y,
#     test_size=0.20,
#     random_state=42,
#     stratify=y        # preserve class balance
# )

# print(f"\nTrain size: {len(y_train)} | Test size: {len(y_test)}")
# print(f"Train scam rate: {y_train.mean():.2%}")
# print(f"Test  scam rate: {y_test.mean():.2%}")

# # ─────────────────────────────────────────────
# # 6. VECTORIZE TEXT
# # ─────────────────────────────────────────────

# vectorizer = TfidfVectorizer(
#     stop_words='english',
#     ngram_range=(1, 3),       # unigrams, bigrams, trigrams for better phrase detection
#     max_features=15000,
#     sublinear_tf=True,         # apply log normalization
#     min_df=1,
# )

# X_train_tfidf = vectorizer.fit_transform(X_text_train)
# X_test_tfidf  = vectorizer.transform(X_text_test)

# # Combine TF-IDF + numeric keyword features
# from scipy.sparse import hstack, csr_matrix

# X_train_num_sparse = csr_matrix(X_num_train.values)
# X_test_num_sparse  = csr_matrix(X_num_test.values)

# X_train_combined = hstack([X_train_tfidf, X_train_num_sparse])
# X_test_combined  = hstack([X_test_tfidf,  X_test_num_sparse])

# # ─────────────────────────────────────────────
# # 7. TRAIN MODEL
# # ─────────────────────────────────────────────

# print("\nTraining model...")

# model = LogisticRegression(
#     C=1.0,
#     max_iter=1000,
#     solver='lbfgs',
#     class_weight='balanced',   # handles class imbalance
#     random_state=42
# )
# model.fit(X_train_combined, y_train)

# # ─────────────────────────────────────────────
# # 8. EVALUATE
# # ─────────────────────────────────────────────

# y_pred      = model.predict(X_test_combined)
# y_pred_prob = model.predict_proba(X_test_combined)[:, 1]

# # Pure ML accuracy
# ml_accuracy = accuracy_score(y_test, y_pred)

# # Final score: ML as primary + keyword as booster, threshold 0.47
# # Lower threshold improves recall (catches more scams) at slight precision cost
# THRESHOLD = 0.47
# kw_scores_test = X_num_test['kw_score'].values
# final_scores   = np.array([
#     final_score(p, k) for p, k in zip(y_pred_prob, kw_scores_test)
# ])
# final_preds    = (final_scores >= THRESHOLD).astype(int)
# final_accuracy = accuracy_score(y_test, final_preds)

# print("\n" + "="*50)
# print("EVALUATION RESULTS")
# print("="*50)
# print(f"ML-only Accuracy:          {ml_accuracy:.4f} ({ml_accuracy*100:.2f}%)")
# print(f"Final Score Accuracy:      {final_accuracy:.4f} ({final_accuracy*100:.2f}%)")
# print(f"Threshold used:            {THRESHOLD}")
# print(f"Formula: ml_prob + 0.15 * keyword_score (capped at 1.0)")
# try:
#     print(f"ROC-AUC Score:             {roc_auc_score(y_test, y_pred_prob):.4f}")
# except:
#     pass
# print("\nClassification Report (Final Score):")
# print(classification_report(y_test, final_preds, target_names=['Normal', 'Scam']))
# print("\nConfusion Matrix:")
# cm = confusion_matrix(y_test, final_preds)
# print(f"  TN={cm[0][0]}  FP={cm[0][1]}")
# print(f"  FN={cm[1][0]}  TP={cm[1][1]}")
# fn_rate = cm[1][0] / (cm[1][0] + cm[1][1]) * 100
# fp_rate = cm[0][1] / (cm[0][0] + cm[0][1]) * 100
# print(f"  False Negative Rate: {fn_rate:.1f}%  (missed scams)")
# print(f"  False Positive Rate: {fp_rate:.1f}%  (false alarms)")
# print("="*50)

# # ─────────────────────────────────────────────
# # 9. SAVE MODELS & KEYWORD CONFIG
# # ─────────────────────────────────────────────

# os.makedirs("models", exist_ok=True)

# joblib.dump(model,      "models/scam_model.pkl")
# joblib.dump(vectorizer, "models/vectorizer.pkl")

# # Save keyword config for use in app.py
# keyword_config = {
#     "groups":       CIALDINI_GROUPS,
#     "combinations": COMBINATIONS
# }
# with open("models/keyword_config.json", "w", encoding="utf-8") as f:
#     json.dump(keyword_config, f, ensure_ascii=False, indent=2)

# print("\nModels saved:")
# print("  models/scam_model.pkl")
# print("  models/vectorizer.pkl")
# print("  models/keyword_config.json")
# print("\nTraining complete!")


"""
train_model.py — Scam Shield Training Pipeline
Incorporates:
  - Cialdini's 11 Principles of Persuasion keyword groups
  - Combination detection from "Principles of Persuasion in Social Engineering"
  - 80/20 train/test split
  - Keyword score capped at 1.0
  - Final score = 0.7 * ML_score + 0.3 * keyword_score
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, roc_auc_score)
from sklearn.pipeline import Pipeline
import joblib
import json
import os

# ─────────────────────────────────────────────
# 1. LOAD & MERGE DATASETS
# ─────────────────────────────────────────────
print("Loading dataset...")

df = pd.read_csv("data/digital_arrest_dataset.csv")
df = df[['text', 'label']].dropna()
df['label'] = df['label'].astype(int)
df['text']  = df['text'].astype(str).str.strip()
df = df[df['text'].str.len() > 5]

print(f"Total samples: {len(df)}")
print(f"  Scam (1):   {(df['label'] == 1).sum()}")
print(f"  Normal (0): {(df['label'] == 0).sum()}")

# ─────────────────────────────────────────────
# 2. CIALDINI KEYWORD GROUPS
#    Source: Cialdini (1984) "Influence: The Psychology of Persuasion"
#    + Workman (2008) "Situational social influence and human behavior"
#    + Gragg (2003) "Phishing" SANS Institute
# ─────────────────────────────────────────────

CIALDINI_GROUPS = {

    # G1 — AUTHORITY (score 0.30)
    # Exploits deference to legitimate-sounding officials
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

# ─────────────────────────────────────────────
# 3. COMBINATION SCORES
#    Based on: "Principles of Persuasion in Social Engineering
#    and Their Use in Phishing" — Ferreira et al. (2015)
#    Descending order of danger
# ─────────────────────────────────────────────

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


def compute_keyword_score(text):
    """
    Compute keyword score based on Cialdini groups + combination bonuses.
    Returns:
      - keyword_score (float, capped at 1.0)
      - groups_hit (set of group names detected)
      - combination_hit (str or None)
    """
    text_lower = text.lower()
    groups_hit = set()
    base_score = 0.0

    for group_name, group_data in CIALDINI_GROUPS.items():
        for kw in group_data["keywords"]:
            if kw in text_lower:
                # Only count each group once for base score
                if group_name not in groups_hit:
                    base_score += group_data["score"]
                    groups_hit.add(group_name)
                break  # one hit per group is enough

    # Check combinations
    combination_bonus = 0.0
    combination_hit = None
    for combo in COMBINATIONS:
        required = set(combo["groups"])
        if required.issubset(groups_hit):
            combination_bonus = max(combination_bonus, combo["bonus"])
            if combination_bonus == combo["bonus"]:
                combination_hit = combo["name"]

    raw = base_score + combination_bonus
    # Cap at 1.0
    keyword_score = min(raw, 1.0)
    return keyword_score, groups_hit, combination_hit


def final_score(ml_prob, keyword_score):
    """
    Keyword is a BOOSTER only — never reduces ML score.
    final = min(ml_prob + 0.10 * keyword_score, 1.0)
    Reduced to 0.10 — keywords have less influence, ML leads.
    """
    boost = 0.10 * keyword_score
    return min(ml_prob + boost, 1.0)


# Safe context words — neutral/greeting utterances that should never be flagged
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
}
MIN_CONFIDENCE = 0.35   # ML must be at least this to flag anything
MIN_TEXT_LEN   = 4      # ignore texts shorter than 4 chars


def is_safe_context(text):
    """
    Returns True if text is too short or dominated by safe/neutral words.
    Prevents hello, okay, happy birthday etc from being flagged.
    """
    text = text.strip()
    if len(text) < MIN_TEXT_LEN:
        return True
    words = set(text.lower().split())
    if words.issubset(SAFE_CONTEXT):
        return True
    if len(words) <= 5 and len(words & SAFE_CONTEXT) / max(len(words), 1) >= 0.7:
        return True
    return False


# ─────────────────────────────────────────────
# 4. FEATURE ENGINEERING
# ─────────────────────────────────────────────

def add_keyword_features(df):
    """Add keyword group hit flags as additional features for training."""
    results = df['text'].apply(lambda t: compute_keyword_score(str(t)))
    df['kw_score']    = results.apply(lambda x: x[0])
    df['kw_groups']   = results.apply(lambda x: len(x[1]))   # count of groups hit
    df['kw_combo']    = results.apply(lambda x: 1 if x[2] else 0)  # combo detected?

    # Individual group flags
    for group_name in CIALDINI_GROUPS.keys():
        df[f'kw_{group_name}'] = df['text'].apply(
            lambda t: 1 if any(
                kw in t.lower()
                for kw in CIALDINI_GROUPS[group_name]['keywords']
            ) else 0
        )
    return df

print("Computing keyword features...")
df = add_keyword_features(df)

# ─────────────────────────────────────────────
# 5. TRAIN / TEST SPLIT — 80 / 20
# ─────────────────────────────────────────────

X_text = df['text']
y      = df['label']

# Additional numeric features
numeric_cols = ['kw_score', 'kw_groups', 'kw_combo'] + \
               [f'kw_{g}' for g in CIALDINI_GROUPS.keys()]
X_numeric = df[numeric_cols]

X_text_train, X_text_test, \
X_num_train,  X_num_test,  \
y_train,      y_test = train_test_split(
    X_text, X_numeric, y,
    test_size=0.20,
    random_state=42,
    stratify=y        # preserve class balance
)

print(f"\nTrain size: {len(y_train)} | Test size: {len(y_test)}")
print(f"Train scam rate: {y_train.mean():.2%}")
print(f"Test  scam rate: {y_test.mean():.2%}")

# ─────────────────────────────────────────────
# 6. VECTORIZE TEXT
# ─────────────────────────────────────────────

vectorizer = TfidfVectorizer(
    stop_words='english',
    ngram_range=(1, 3),       # unigrams, bigrams, trigrams for better phrase detection
    max_features=15000,
    sublinear_tf=True,         # apply log normalization
    min_df=1,
)

X_train_tfidf = vectorizer.fit_transform(X_text_train)
X_test_tfidf  = vectorizer.transform(X_text_test)

# Combine TF-IDF + numeric keyword features
from scipy.sparse import hstack, csr_matrix

X_train_num_sparse = csr_matrix(X_num_train.values)
X_test_num_sparse  = csr_matrix(X_num_test.values)

X_train_combined = hstack([X_train_tfidf, X_train_num_sparse])
X_test_combined  = hstack([X_test_tfidf,  X_test_num_sparse])

# ─────────────────────────────────────────────
# 7. TRAIN MODEL
# ─────────────────────────────────────────────

print("\nTraining model...")

model = LogisticRegression(
    C=1.0,
    max_iter=1000,
    solver='lbfgs',
    class_weight='balanced',   # handles class imbalance
    random_state=42
)
model.fit(X_train_combined, y_train)

# ─────────────────────────────────────────────
# 8. EVALUATE
# ─────────────────────────────────────────────

y_pred      = model.predict(X_test_combined)
y_pred_prob = model.predict_proba(X_test_combined)[:, 1]

# Pure ML accuracy
ml_accuracy = accuracy_score(y_test, y_pred)

# Final score: ML primary + keyword booster, threshold 0.52
# Slightly stricter than before to reduce false positives on neutral speech
THRESHOLD = 0.38
kw_scores_test = X_num_test['kw_score'].values
texts_test     = X_text_test.values

final_scores = []
for prob, kw, txt in zip(y_pred_prob, kw_scores_test, texts_test):
    if is_safe_context(str(txt)) or prob < MIN_CONFIDENCE:
        final_scores.append(0.0)   # force safe for neutral/short text
    else:
        final_scores.append(final_score(prob, kw))

final_scores = np.array(final_scores)
final_preds  = (final_scores >= THRESHOLD).astype(int)
final_accuracy = accuracy_score(y_test, final_preds)

print("\n" + "="*50)
print("EVALUATION RESULTS")
print("="*50)
print(f"ML-only Accuracy:          {ml_accuracy:.4f} ({ml_accuracy*100:.2f}%)")
print(f"Final Score Accuracy:      {final_accuracy:.4f} ({final_accuracy*100:.2f}%)")
print(f"Threshold used:            {THRESHOLD}")
print(f"Formula: ml_prob + 0.10 * keyword_score (capped at 1.0)")
try:
    print(f"ROC-AUC Score:             {roc_auc_score(y_test, y_pred_prob):.4f}")
except:
    pass
print("\nClassification Report (Final Score):")
print(classification_report(y_test, final_preds, target_names=['Normal', 'Scam']))
print("\nConfusion Matrix:")
cm = confusion_matrix(y_test, final_preds)
print(f"  TN={cm[0][0]}  FP={cm[0][1]}")
print(f"  FN={cm[1][0]}  TP={cm[1][1]}")
fn_rate = cm[1][0] / (cm[1][0] + cm[1][1]) * 100
fp_rate = cm[0][1] / (cm[0][0] + cm[0][1]) * 100
print(f"  False Negative Rate: {fn_rate:.1f}%  (missed scams)")
print(f"  False Positive Rate: {fp_rate:.1f}%  (false alarms)")
print("="*50)

# ─────────────────────────────────────────────
# 9. SAVE MODELS & KEYWORD CONFIG
# ─────────────────────────────────────────────

os.makedirs("models", exist_ok=True)

joblib.dump(model,      "models/scam_model.pkl")
joblib.dump(vectorizer, "models/vectorizer.pkl")

# Save keyword config for use in app.py
keyword_config = {
    "groups":       CIALDINI_GROUPS,
    "combinations": COMBINATIONS
}
with open("models/keyword_config.json", "w", encoding="utf-8") as f:
    json.dump(keyword_config, f, ensure_ascii=False, indent=2)

print("\nModels saved:")
print("  models/scam_model.pkl")
print("  models/vectorizer.pkl")
print("  models/keyword_config.json")
print("\nTraining complete!")