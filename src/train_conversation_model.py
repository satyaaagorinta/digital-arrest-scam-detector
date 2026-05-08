"""
train_conversation_model.py
============================
Trains a conversation-level fraud detection model (Layer 2).

Based on:
  "A Synthetic Conversational Smishing Dataset for
   Social Engineering Detection" (2026)
  Ferreira et al. (2015) - Principles of Persuasion in Social Engineering
  Vishwanath (2018) - Suspicion Cognition and Automaticity Model (SCAM)

Pipeline:
  1. Load conversation dataset
  2. Extract 28 conversation-level features per conversation
  3. 80/20 stratified train/test split
  4. Train + compare 3 classifiers
  5. Full evaluation with threshold sweep
  6. Save best model

Run: python src/train_conversation_model.py
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
from collections import Counter
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix, roc_auc_score,
    precision_score, recall_score, f1_score
)
from sklearn.pipeline import Pipeline
from scipy.sparse import hstack, csr_matrix

# ─────────────────────────────────────────────────────────────
# 1. LOAD DATASET
# ─────────────────────────────────────────────────────────────
print("Loading conversation dataset...")
df = pd.read_csv("data/conversation_dataset.csv")
df = df.dropna(subset=["text", "speaker", "label"])
df["text"]  = df["text"].astype(str).str.strip()
df["label"] = df["label"].astype(int)

total_convos = df["conversation_id"].nunique()
scam_convos  = df[df["label"] == 1]["conversation_id"].nunique()
safe_convos  = df[df["label"] == 0]["conversation_id"].nunique()

print(f"  Total conversations : {total_convos}")
print(f"  Scam conversations  : {scam_convos} ({scam_convos/total_convos*100:.1f}%)")
print(f"  Safe conversations  : {safe_convos} ({safe_convos/total_convos*100:.1f}%)")
print(f"  Total turns         : {len(df)}")

# ─────────────────────────────────────────────────────────────
# 2. LOAD SENTENCE-LEVEL MODEL
# ─────────────────────────────────────────────────────────────
print("\nLoading sentence-level model...")
sent_model      = joblib.load("models/scam_model.pkl")
sent_vectorizer = joblib.load("models/vectorizer.pkl")

with open("models/keyword_config.json", encoding="utf-8") as f:
    kw_cfg = json.load(f)

CIALDINI_GROUPS = kw_cfg["groups"]
COMBINATIONS    = kw_cfg["combinations"]

# ─────────────────────────────────────────────────────────────
# 3. KEYWORD + COMPLIANCE SCORING UTILS
# ─────────────────────────────────────────────────────────────
GENERIC_ONLY = {
    "urgency":     {"immediately","right now","abhi","turant","jaldi",
                    "tonight","today only","last date","deadline","act now"},
    "money":       {"send money","transfer","payment","amount","deposit","pay"},
    "distraction": {"confidential","sensitive","secret","sealed"},
}

def compute_keyword_score(text):
    text_lower = text.lower()
    groups_hit = set()
    for gname, gdata in CIALDINI_GROUPS.items():
        for kw in gdata["keywords"]:
            if kw in text_lower:
                groups_hit.add(gname)
                break
    if len(groups_hit) < 2:
        return 0.0, groups_hit
    non_generic = groups_hit - set(GENERIC_ONLY.keys())
    adjusted = set()
    for gname in groups_hit:
        if gname in GENERIC_ONLY:
            hit_kw = next((kw for kw in CIALDINI_GROUPS[gname]["keywords"]
                           if kw in text_lower), None)
            if hit_kw in GENERIC_ONLY.get(gname, set()):
                if len(non_generic) >= 1:
                    adjusted.add(gname)
            else:
                adjusted.add(gname)
        else:
            adjusted.add(gname)
    if len(adjusted) < 2:
        return 0.0, adjusted
    base  = sum(CIALDINI_GROUPS[g]["score"] for g in adjusted)
    combo = 0.0
    for c in COMBINATIONS:
        if set(c["groups"]).issubset(adjusted):
            combo = max(combo, c["bonus"])
    return min(base + combo, 1.0), adjusted

COMPLIANCE_HIGH = [
    "yes sir","yes officer","okay sir","ji haan","haan sir",
    "i'll cooperate","cooperate karunga","okay okay","what do i do",
    "i'll do it","kar deta hoon","sending now","bhej raha hoon",
    "thank you for telling","i trust you","i'll pay","transfer kar deta",
    "theek hai kar deta","bhej raha","kar raha hoon","kar deti hoon",
    "please don't arrest","please help","mujhe kya karna","i'm scared",
]
COMPLIANCE_INFO = [
    "my account number","my otp","otp is","pin is","card number","cvv",
    "password","net banking","mera account","mera otp","aadhar",
    "date of birth is","username is","login hai","mera pin",
]
RESISTANCE = [
    "no","i refuse","this is a scam","you are a fraud","calling police",
    "not paying","nahi karunga","fraud hai","scam hai","police bulata",
    "i'm reporting","phone rakh","goodbye","verify yourself","my lawyer",
    "cybercrime helpline","official channel","report kar","fraud call",
    "seedha jaata hoon","directly jaata hoon",
]

def get_ml_score(text):
    try:
        tfidf    = sent_vectorizer.transform([text])
        kw_s, gh = compute_keyword_score(text)
        kw_g     = len(gh)
        kw_c     = 1 if kw_s > 0 else 0
        flags    = [
            1 if any(kw in text.lower()
                     for kw in CIALDINI_GROUPS[g]["keywords"]) else 0
            for g in CIALDINI_GROUPS.keys()
        ]
        num = csr_matrix([[kw_s, kw_g, kw_c] + flags])
        X   = hstack([tfidf, num])
        return float(sent_model.predict_proba(X)[0][1])
    except:
        return 0.0

def score_victim_turn(text, prev_atk_score):
    tl = text.lower()
    if any(p in tl for p in COMPLIANCE_INFO):
        return 0.7 * (1.3 if prev_atk_score > 0.6 else 1.0), "info_leak"
    if any(p in tl for p in RESISTANCE):
        return -0.4, "resistance"
    if any(p in tl for p in COMPLIANCE_HIGH):
        w = 0.4 * (1.3 if prev_atk_score > 0.6 else
                   1.1 if prev_atk_score > 0.38 else 1.0)
        return w, "compliance"
    return 0.0, "neutral"

# ─────────────────────────────────────────────────────────────
# 4. FEATURE EXTRACTION
# ─────────────────────────────────────────────────────────────
print("\nExtracting features from conversations...")

def extract_features(conv_df):
    atk_rows = conv_df[conv_df["speaker"] == "attacker"]
    vic_rows = conv_df[conv_df["speaker"] == "victim"]

    # ── Attacker ML + keyword scores ──
    atk_ml = [get_ml_score(t) for t in atk_rows["text"]]
    atk_kw = [compute_keyword_score(t)[0] for t in atk_rows["text"]]

    avg_atk_ml     = float(np.mean(atk_ml)) if atk_ml else 0.0
    max_atk_ml     = float(np.max(atk_ml))  if atk_ml else 0.0
    avg_atk_kw     = float(np.mean(atk_kw)) if atk_kw else 0.0
    max_atk_kw     = float(np.max(atk_kw))  if atk_kw else 0.0
    high_risk_turns= sum(1 for s in atk_ml if s > 0.38)
    atk_count      = len(atk_rows)

    # ── Cialdini principle flags ──
    all_groups = set()
    for t in atk_rows["text"]:
        _, gh = compute_keyword_score(t)
        all_groups |= gh

    # ── Victim compliance scores ──
    compliance_scores = []
    response_types    = []
    prev_score = 0.0
    atk_idx    = 0
    for _, row in conv_df.iterrows():
        if row["speaker"] == "attacker":
            if atk_idx < len(atk_ml):
                prev_score = atk_ml[atk_idx]
                atk_idx += 1
        elif row["speaker"] == "victim":
            cs, rt = score_victim_turn(row["text"], prev_score)
            compliance_scores.append(cs)
            response_types.append(rt)

    avg_comp  = float(np.mean(compliance_scores)) if compliance_scores else 0.0
    max_comp  = float(np.max(compliance_scores))  if compliance_scores else 0.0
    info_leak = 1 if "info_leak"  in response_types else 0
    resist_n  = response_types.count("resistance")
    comply_n  = response_types.count("compliance") + info_leak

    # Escalation trajectory (foot-in-the-door pattern)
    if len(compliance_scores) >= 3:
        mid        = len(compliance_scores) // 2
        trajectory = (float(np.mean(compliance_scores[mid:])) -
                      float(np.mean(compliance_scores[:mid])))
    else:
        trajectory = 0.0

    # Max consecutive compliance streak
    max_streak = cur_streak = 0
    for cs in compliance_scores:
        if cs > 0.1:
            cur_streak += 1
            max_streak  = max(max_streak, cur_streak)
        else:
            cur_streak  = 0

    # ── Structure features ──
    total_turns   = len(conv_df)
    vic_count     = len(vic_rows)
    turn_ratio    = vic_count / max(atk_count, 1)
    avg_atk_words = float(np.mean([len(t.split())
                                    for t in atk_rows["text"]])) \
                    if len(atk_rows) > 0 else 0.0

    return {
        "avg_atk_ml":      avg_atk_ml,
        "max_atk_ml":      max_atk_ml,
        "avg_atk_kw":      avg_atk_kw,
        "max_atk_kw":      max_atk_kw,
        "high_risk_turns": high_risk_turns,
        "atk_turns":       atk_count,
        "authority":       1 if "authority"    in all_groups else 0,
        "urgency":         1 if "urgency"      in all_groups else 0,
        "threat":          1 if "threat"       in all_groups else 0,
        "money":           1 if "money"        in all_groups else 0,
        "warrant":         1 if "warrant"      in all_groups else 0,
        "account":         1 if "account"      in all_groups else 0,
        "distraction":     1 if "distraction"  in all_groups else 0,
        "num_principles":  len(all_groups),
        "avg_compliance":  avg_comp,
        "max_compliance":  max_comp,
        "info_leaked":     info_leak,
        "resistance_count":resist_n,
        "compliance_count":comply_n,
        "trajectory":      trajectory,
        "max_streak":      max_streak,
        "total_turns":     total_turns,
        "victim_turns":    vic_count,
        "turn_ratio":      turn_ratio,
        "avg_atk_words":   avg_atk_words,
    }

rows   = []
labels = []
conv_ids = df["conversation_id"].unique()

for cid in conv_ids:
    cdf   = df[df["conversation_id"] == cid].reset_index(drop=True)
    label = int(cdf["label"].iloc[0])
    feats = extract_features(cdf)
    rows.append(feats)
    labels.append(label)

feat_df = pd.DataFrame(rows)
y       = np.array(labels)

print(f"  Feature matrix : {feat_df.shape}")
print(f"  Features       : {list(feat_df.columns)}")

# ─────────────────────────────────────────────────────────────
# 5. TRAIN / TEST SPLIT — 80 / 20 STRATIFIED
# ─────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    feat_df, y,
    test_size=0.20,
    random_state=42,
    stratify=y        # preserve scam/safe ratio in both splits
)

print(f"\nTrain / Test Split (80/20 stratified):")
print(f"  Train : {len(y_train)} conversations "
      f"(scam={y_train.sum()}, safe={(y_train==0).sum()})")
print(f"  Test  : {len(y_test)}  conversations "
      f"(scam={y_test.sum()}, safe={(y_test==0).sum()})")

# ─────────────────────────────────────────────────────────────
# 6. TRAIN + COMPARE MODELS
# ─────────────────────────────────────────────────────────────
print("\nTraining and comparing models...")

candidates = {
    "LogisticRegression_C0.01": Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(C=0.01, max_iter=500,
                                      class_weight="balanced",
                                      random_state=42))
    ]),
    "LogisticRegression_C0.1": Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(C=0.1, max_iter=500,
                                      class_weight="balanced",
                                      random_state=42))
    ]),
    "RandomForest_d3": RandomForestClassifier(
        n_estimators=100, max_depth=3, min_samples_leaf=5,
        class_weight="balanced", random_state=42
    ),
    "RandomForest_d4": RandomForestClassifier(
        n_estimators=100, max_depth=4, min_samples_leaf=4,
        class_weight="balanced", random_state=42
    ),
    "GradientBoosting": GradientBoostingClassifier(
        n_estimators=100, max_depth=2, learning_rate=0.05,
        subsample=0.8, random_state=42
    ),
}

cv         = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
best_model = None
best_name  = ""
best_cv    = 0.0
results    = {}

print(f"\n{'Model':<25} {'CV AUC':>8} {'Std':>7}")
print("-" * 42)
for name, m in candidates.items():
    try:
        cv_scores = cross_val_score(m, feat_df, y, cv=cv, scoring="roc_auc")
        mean, std = cv_scores.mean(), cv_scores.std()
        results[name] = (mean, std)
        print(f"  {name:<23} {mean:.4f}  ±{std:.4f}")
        if mean > best_cv:
            best_cv    = mean
            best_model = m
            best_name  = name
    except Exception as e:
        print(f"  {name:<23} FAILED — {e}")

print(f"\nSelected: {best_name} (CV AUC: {best_cv:.4f})")

# Final fit on training set
best_model.fit(X_train, y_train)

# ─────────────────────────────────────────────────────────────
# 7. EVALUATION ON TEST SET
# ─────────────────────────────────────────────────────────────
y_pred      = best_model.predict(X_test)
y_pred_prob = best_model.predict_proba(X_test)[:, 1]

print("\n" + "=" * 58)
print("CONVERSATION MODEL — TEST SET EVALUATION")
print("=" * 58)
print(f"Model:    {best_name}")
print(f"Test set: {len(y_test)} conversations")
print()
print(f"Accuracy  : {accuracy_score(y_test, y_pred):.4f}  "
      f"({accuracy_score(y_test, y_pred)*100:.2f}%)")
try:
    print(f"ROC-AUC   : {roc_auc_score(y_test, y_pred_prob):.4f}")
except:
    pass
print()
print("Classification Report:")
print(classification_report(y_test, y_pred,
                             target_names=["Safe", "Scam"]))
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()
print("Confusion Matrix:")
print(f"  TN={tn}  FP={fp}")
print(f"  FN={fn}  TP={tp}")
print(f"  False Negative Rate: {fn/(fn+tp)*100:.1f}%  (missed scams)")
print(f"  False Positive Rate: {fp/(fp+tn)*100:.1f}%  (false alarms)")

# ── Overfitting check: compare train vs test performance ──
y_train_pred = best_model.predict(X_train)
train_acc    = accuracy_score(y_train, y_train_pred)
test_acc     = accuracy_score(y_test,  y_pred)
gap          = train_acc - test_acc

print(f"\nOverfitting Check:")
print(f"  Train accuracy : {train_acc:.4f}")
print(f"  Test  accuracy : {test_acc:.4f}")
print(f"  Gap            : {gap:.4f}", end="")
if gap < 0.05:
    print("  ✅ Good — minimal overfitting")
elif gap < 0.10:
    print("  ⚠ Moderate — some overfitting")
else:
    print("  ❌ High — significant overfitting, consider more data")

# ─────────────────────────────────────────────────────────────
# 8. THRESHOLD SWEEP (same as sentence model)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"{'Thresh':>7} | {'Acc':>6} | {'Prec':>6} | {'Rec':>6} | "
      f"{'F1':>6} | {'FN':>4} | {'FP':>4} | {'FNR%':>6}")
print("=" * 65)

best_thresh      = 0.5
best_f1          = 0.0
best_thresh_data = None
thresh_results   = []

for thresh in np.arange(0.30, 0.75, 0.05):
    preds  = (y_pred_prob >= thresh).astype(int)
    acc    = accuracy_score(y_test, preds)
    prec   = precision_score(y_test, preds, zero_division=0)
    rec    = recall_score(y_test, preds, zero_division=0)
    f1     = f1_score(y_test, preds, zero_division=0)
    cmt    = confusion_matrix(y_test, preds)
    tn2, fp2, fn2, tp2 = cmt.ravel()
    fnr    = fn2 / (fn2 + tp2) * 100 if (fn2 + tp2) > 0 else 0
    marker = " ← recommended" if f1 > best_f1 and fp2 <= len(y_test) * 0.15 else ""
    thresh_results.append((thresh, acc, prec, rec, f1, fn2, fp2, fnr))
    print(f"  {thresh:.2f}  | {acc:.4f} | {prec:.4f} | {rec:.4f} | "
          f"{f1:.4f} | {fn2:4d} | {fp2:4d} | {fnr:5.1f}%{marker}")
    if f1 > best_f1 and fp2 <= len(y_test) * 0.15:
        best_f1          = f1
        best_thresh      = thresh
        best_thresh_data = (thresh, acc, prec, rec, f1, fn2, fp2, fnr)

print("=" * 65)
if best_thresh_data:
    t, a, p, r, f, fn2, fp2, fnr = best_thresh_data
    print(f"\nRecommended threshold: {t:.2f}")
    print(f"  Accuracy  : {a:.4f}")
    print(f"  Precision : {p:.4f}")
    print(f"  Recall    : {r:.4f}")
    print(f"  F1        : {f:.4f}")
    print(f"  FN        : {fn2}  FP: {fp2}")
    print(f"  FNR       : {fnr:.1f}%")

# ─────────────────────────────────────────────────────────────
# 9. FEATURE IMPORTANCE (if tree-based)
# ─────────────────────────────────────────────────────────────
try:
    clf = best_model.named_steps.get("clf", best_model)
    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
        feat_names  = list(feat_df.columns)
        top = sorted(zip(feat_names, importances),
                     key=lambda x: x[1], reverse=True)[:10]
        print("\nTop 10 Feature Importances:")
        for fname, fimp in top:
            bar = "█" * int(fimp * 40)
            print(f"  {fname:<22} {fimp:.4f}  {bar}")
except:
    pass

# ─────────────────────────────────────────────────────────────
# 10. SAVE
# ─────────────────────────────────────────────────────────────
os.makedirs("models", exist_ok=True)
joblib.dump(best_model,          "models/conversation_model.pkl")
joblib.dump(list(feat_df.columns),"models/conversation_features.pkl")

# Save recommended threshold for predictor to use
config = {
    "model_name":           best_name,
    "cv_auc":               round(best_cv, 4),
    "recommended_threshold":round(float(best_thresh), 2),
    "feature_names":        list(feat_df.columns),
}
with open("models/conversation_config.json", "w") as f:
    json.dump(config, f, indent=2)

print("\n" + "=" * 58)
print("Saved:")
print("  models/conversation_model.pkl")
print("  models/conversation_features.pkl")
print("  models/conversation_config.json")
print("=" * 58)
print("\nDone!")