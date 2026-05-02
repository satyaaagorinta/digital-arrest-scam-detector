"""
Threshold optimizer — tests multiple thresholds and recommends the best one
Run: python src/threshold_test.py
"""
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, confusion_matrix, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix
import json

# ── Load model + config ──────────────────────────────────────────────────────
model      = joblib.load("models/scam_model.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

with open("models/keyword_config.json", encoding="utf-8") as f:
    cfg = json.load(f)

CIALDINI_GROUPS = cfg["groups"]
COMBINATIONS    = cfg["combinations"]

# ── Keyword scoring ──────────────────────────────────────────────────────────
def compute_keyword_score(text):
    text_lower  = text.lower()
    groups_hit  = set()
    base_score  = 0.0
    for gname, gdata in CIALDINI_GROUPS.items():
        for kw in gdata["keywords"]:
            if kw in text_lower:
                if gname not in groups_hit:
                    base_score += gdata["score"]
                    groups_hit.add(gname)
                break
    combo_bonus = 0.0
    for combo in COMBINATIONS:
        if set(combo["groups"]).issubset(groups_hit):
            combo_bonus = max(combo_bonus, combo["bonus"])
    return min(base_score + combo_bonus, 1.0), groups_hit

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

# ── Build feature matrix ─────────────────────────────────────────────────────
df = pd.read_csv("data/digital_arrest_dataset.csv")
df = df[['text','label']].dropna()
df['text']  = df['text'].astype(str).str.strip()
df['label'] = df['label'].astype(int)
df = df[df['text'].str.len() > 5]

_, X_test, _, y_test = train_test_split(
    df['text'], df['label'], test_size=0.20,
    random_state=42, stratify=df['label']
)

group_names = list(CIALDINI_GROUPS.keys())

def build_features(texts):
    tfidf = vectorizer.transform(texts)
    rows  = []
    for t in texts:
        kw_score, groups_hit = compute_keyword_score(str(t))
        flags = [1 if any(kw in str(t).lower() for kw in CIALDINI_GROUPS[g]["keywords"]) else 0
                 for g in group_names]
        rows.append([kw_score, len(groups_hit), 1 if kw_score > 0 else 0] + flags)
    return hstack([tfidf, csr_matrix(rows)])

print("Building features...")
X = build_features(X_test.tolist())
probs = model.predict_proba(X)[:,1]

# Apply safe-context gate + min confidence (forces prob to 0 for neutral text)
probs_gated = np.array([
    0.0 if (is_safe_context(str(t)) or p < MIN_CONFIDENCE) else p
    for t, p in zip(X_test, probs)
])

# Final scores with keyword boost
kw_scores = []
for t in X_test:
    ks, _ = compute_keyword_score(str(t))
    kw_scores.append(ks)
kw_scores = np.array(kw_scores)

KW_WEIGHT = 0.10
final_scores = np.minimum(probs_gated + KW_WEIGHT * kw_scores, 1.0)

# ── Test multiple thresholds ─────────────────────────────────────────────────
print("\n" + "="*72)
print(f"{'Thresh':>7} | {'Acc':>6} | {'Prec':>6} | {'Rec':>6} | {'F1':>6} | {'FN':>4} | {'FP':>4} | {'FNR%':>6}")
print("="*72)

results = []
for thresh in np.arange(0.30, 0.71, 0.02):
    preds = (final_scores >= thresh).astype(int)
    acc   = accuracy_score(y_test, preds)
    prec  = precision_score(y_test, preds, zero_division=0)
    rec   = recall_score(y_test, preds, zero_division=0)
    f1    = f1_score(y_test, preds, zero_division=0)
    cm    = confusion_matrix(y_test, preds)
    tn, fp, fn, tp = cm.ravel()
    fnr   = fn / (fn + tp) * 100
    results.append((thresh, acc, prec, rec, f1, fn, fp, fnr))
    marker = " ◄ current" if abs(thresh - 0.52) < 0.01 else ""
    print(f"  {thresh:.2f}  | {acc:.4f} | {prec:.4f} | {rec:.4f} | {f1:.4f} | {fn:4d} | {fp:4d} | {fnr:5.1f}%{marker}")

print("="*72)

# ── Recommend best threshold ─────────────────────────────────────────────────
# Priority: maximize F1 for scam class, while keeping FP <= 10
best = max(
    [r for r in results if r[6] <= 10],   # FP constraint
    key=lambda r: (r[4], r[3])            # sort by F1 then recall
)
print(f"\n✅ RECOMMENDED THRESHOLD: {best[0]:.2f}")
print(f"   Accuracy:  {best[1]:.4f}")
print(f"   Precision: {best[2]:.4f}")
print(f"   Recall:    {best[3]:.4f}")
print(f"   F1:        {best[4]:.4f}")
print(f"   FN:        {best[5]}  FP: {best[6]}")
print(f"   FNR:       {best[7]:.1f}%")
print()
print("Rationale: best F1+recall while keeping false alarms (FP) <= 10")