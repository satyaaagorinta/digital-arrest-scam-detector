"""
predict_conversation.py
========================
Standalone conversation-level fraud predictor.
Combines sentence-level ML scores with conversation-level model.

Usage:
    from src.predict_conversation import ConversationPredictor
    predictor = ConversationPredictor()
    result = predictor.predict(conversation_log)
"""

import joblib
import json
import numpy as np
from scipy.sparse import hstack, csr_matrix


class ConversationPredictor:
    """
    Two-layer fraud detection:
    Layer 1: Sentence-level ML (existing scam_model.pkl)
    Layer 2: Conversation-level ML (conversation_model.pkl)
    Combined using weighted ensemble.
    """

    def __init__(self,
                 sent_model_path="models/scam_model.pkl",
                 sent_vec_path="models/vectorizer.pkl",
                 conv_model_path="models/conversation_model.pkl",
                 conv_feats_path="models/conversation_features.pkl",
                 kw_config_path="models/keyword_config.json"):

        self.sent_model      = joblib.load(sent_model_path)
        self.sent_vectorizer = joblib.load(sent_vec_path)
        self.conv_model      = joblib.load(conv_model_path)
        self.feature_names   = joblib.load(conv_feats_path)

        with open(kw_config_path, encoding="utf-8") as f:
            kw_cfg = json.load(f)
        self.CIALDINI_GROUPS = kw_cfg["groups"]
        self.COMBINATIONS    = kw_cfg["combinations"]

        self.GENERIC_ONLY = {
            "urgency":     {"immediately","right now","abhi","turant","jaldi",
                            "tonight","today only","last date","deadline","act now"},
            "money":       {"send money","transfer","payment","amount","deposit","pay"},
            "distraction": {"confidential","sensitive","secret","sealed"},
        }

        self.COMPLIANCE_HIGH = [
            "yes sir","yes officer","okay sir","ji haan","haan sir",
            "i'll cooperate","cooperate karunga","okay okay","what do i do",
            "i'll do it","kar deta hoon","sending now","bhej raha hoon",
            "thank you for telling","i trust you","i'll pay","transfer kar deta"
        ]
        self.COMPLIANCE_INFO = [
            "my account number","my otp","my pin","otp is","pin is",
            "card number","cvv","password","net banking","mera account",
            "mera otp","aadhar","date of birth is","username is"
        ]
        self.RESISTANCE = [
            "no","i refuse","this is a scam","you are a fraud","calling police",
            "not paying","nahi karunga","fraud hai","scam hai","police bulata",
            "i'm reporting","phone rakh","goodbye","verify yourself","my lawyer"
        ]

    # ── Keyword scoring ──────────────────────────────────────────────────────
    def _keyword_score(self, text):
        text_lower = text.lower()
        groups_hit = set()
        for gname, gdata in self.CIALDINI_GROUPS.items():
            for kw in gdata["keywords"]:
                if kw in text_lower:
                    groups_hit.add(gname)
                    break
        if len(groups_hit) < 2:
            return 0.0, groups_hit
        non_generic = groups_hit - set(self.GENERIC_ONLY.keys())
        adjusted = set()
        for gname in groups_hit:
            if gname in self.GENERIC_ONLY:
                hit_kw = next((kw for kw in self.CIALDINI_GROUPS[gname]["keywords"]
                               if kw in text_lower), None)
                if hit_kw in self.GENERIC_ONLY.get(gname, set()):
                    if len(non_generic) >= 1:
                        adjusted.add(gname)
                else:
                    adjusted.add(gname)
            else:
                adjusted.add(gname)
        if len(adjusted) < 2:
            return 0.0, adjusted
        base = sum(self.CIALDINI_GROUPS[g]["score"] for g in adjusted)
        combo = 0.0
        for c in self.COMBINATIONS:
            if set(c["groups"]).issubset(adjusted):
                combo = max(combo, c["bonus"])
        return min(base + combo, 1.0), adjusted

    # ── Sentence ML score ────────────────────────────────────────────────────
    def _sent_ml_score(self, text):
        try:
            tfidf    = self.sent_vectorizer.transform([text])
            kw_s, gh = self._keyword_score(text)
            kw_g     = len(gh)
            kw_c     = 1 if kw_s > 0 else 0
            flags    = [
                1 if any(kw in text.lower()
                         for kw in self.CIALDINI_GROUPS[g]["keywords"]) else 0
                for g in self.CIALDINI_GROUPS.keys()
            ]
            num   = csr_matrix([[kw_s, kw_g, kw_c] + flags])
            X     = hstack([tfidf, num])
            return float(self.sent_model.predict_proba(X)[0][1])
        except:
            return 0.0

    # ── Victim compliance score ──────────────────────────────────────────────
    def _victim_score(self, text, prev_atk_score):
        tl = text.lower()
        if any(p in tl for p in self.COMPLIANCE_INFO):
            return 0.7 * (1.3 if prev_atk_score > 0.6 else 1.0), "info_leak"
        if any(p in tl for p in self.RESISTANCE):
            return -0.4, "resistance"
        if any(p in tl for p in self.COMPLIANCE_HIGH):
            w = 0.4 * (1.3 if prev_atk_score > 0.6 else
                       1.1 if prev_atk_score > 0.38 else 1.0)
            return w, "compliance"
        return 0.0, "neutral"

    # ── Feature extraction ───────────────────────────────────────────────────
    def _extract_features(self, conversation):
        """
        conversation: list of dicts with keys 'speaker' and 'text'
        """
        attacker_turns = [t for t in conversation if t["speaker"] == "attacker"]
        victim_turns   = [t for t in conversation if t["speaker"] == "victim"]

        atk_ml = [self._sent_ml_score(t["text"]) for t in attacker_turns]
        atk_kw = [self._keyword_score(t["text"])[0] for t in attacker_turns]

        avg_atk_ml     = np.mean(atk_ml) if atk_ml else 0
        max_atk_ml     = np.max(atk_ml)  if atk_ml else 0
        avg_atk_kw     = np.mean(atk_kw) if atk_kw else 0
        max_atk_kw     = np.max(atk_kw)  if atk_kw else 0
        high_risk_turns= sum(1 for s in atk_ml if s > 0.38)
        atk_turns_cnt  = len(attacker_turns)

        all_groups = set()
        for t in attacker_turns:
            _, gh = self._keyword_score(t["text"])
            all_groups |= gh

        compliance_scores = []
        response_types    = []
        prev_score = 0.0
        atk_idx    = 0
        for turn in conversation:
            if turn["speaker"] == "attacker":
                if atk_idx < len(atk_ml):
                    prev_score = atk_ml[atk_idx]
                    atk_idx += 1
            elif turn["speaker"] == "victim":
                cs, rt = self._victim_score(turn["text"], prev_score)
                compliance_scores.append(cs)
                response_types.append(rt)

        avg_compliance = np.mean(compliance_scores) if compliance_scores else 0
        max_compliance = np.max(compliance_scores)  if compliance_scores else 0
        info_leaked    = 1 if "info_leak"  in response_types else 0
        resistance_cnt = response_types.count("resistance")
        compliance_cnt = response_types.count("compliance") + info_leaked

        if len(compliance_scores) >= 3:
            mid        = len(compliance_scores) // 2
            trajectory = np.mean(compliance_scores[mid:]) - np.mean(compliance_scores[:mid])
        else:
            trajectory = 0.0

        max_streak = cur_streak = 0
        for cs in compliance_scores:
            if cs > 0.1:
                cur_streak += 1
                max_streak = max(max_streak, cur_streak)
            else:
                cur_streak = 0

        total_turns   = len(conversation)
        victim_turns_n= len(victim_turns)
        turn_ratio    = victim_turns_n / max(atk_turns_cnt, 1)
        avg_atk_words = np.mean([len(t["text"].split()) for t in attacker_turns]) \
                        if attacker_turns else 0

        feats = {
            "avg_atk_ml":         avg_atk_ml,
            "max_atk_ml":         max_atk_ml,
            "avg_atk_kw":         avg_atk_kw,
            "max_atk_kw":         max_atk_kw,
            "high_risk_turns":    high_risk_turns,
            "atk_turns":          atk_turns_cnt,
            "authority":          1 if "authority"   in all_groups else 0,
            "urgency":            1 if "urgency"     in all_groups else 0,
            "threat":             1 if "threat"      in all_groups else 0,
            "money":              1 if "money"       in all_groups else 0,
            "warrant":            1 if "warrant"     in all_groups else 0,
            "account":            1 if "account"     in all_groups else 0,
            "distraction":        1 if "distraction" in all_groups else 0,
            "num_principles":     len(all_groups),
            "avg_compliance":     avg_compliance,
            "max_compliance":     max_compliance,
            "info_leaked":        info_leaked,
            "resistance_count":   resistance_cnt,
            "compliance_count":   compliance_cnt,
            "trajectory":         trajectory,
            "max_streak":         max_streak,
            "total_turns":        total_turns,
            "victim_turns":       victim_turns_n,
            "turn_ratio":         turn_ratio,
            "avg_atk_words":      avg_atk_words,
        }
        return feats, atk_ml, compliance_scores, response_types, all_groups

    # ── Main predict method ──────────────────────────────────────────────────
    def predict(self, conversation):
        """
        Predict fraud risk for a full conversation.

        Args:
            conversation: list of {'speaker': 'attacker'|'victim', 'text': str}

        Returns:
            dict with:
                ml2_score       — conversation model probability (Layer 2)
                ml1_avg_score   — average sentence ML score (Layer 1)
                combined_score  — weighted ensemble of both layers
                verdict         — human-readable verdict
                color           — UI color code
                breakdown       — detailed feature breakdown
                info_disclosed  — bool
                dominant_principles — list of top Cialdini groups used
        """
        if not conversation:
            return None

        feats, atk_ml, comp_scores, resp_types, groups = \
            self._extract_features(conversation)

        # Align features to trained model's feature order
        feat_vec = np.array([[feats.get(f, 0.0) for f in self.feature_names]])

        # Layer 2 — conversation model
        ml2_prob = float(self.conv_model.predict_proba(feat_vec)[0][1])

        # Layer 1 summary
        ml1_avg  = float(np.mean(atk_ml)) if atk_ml else 0.0
        ml1_peak = float(np.max(atk_ml))  if atk_ml else 0.0

        # ── Weighted ensemble ──
        # Layer 2 (conversation context) weighted higher — it sees full picture
        combined = round(min(0.55 * ml2_prob + 0.45 * ml1_avg, 1.0), 3)

        # Critical override — info disclosure always high risk
        if feats["info_leaked"]:
            combined = max(combined, 0.80)

        # Verdict
        info_disclosed = bool(feats["info_leaked"])
        if info_disclosed:
            verdict, color = "CRITICAL — Information Disclosed", "#cc0000"
        elif combined > 0.65:
            verdict, color = "HIGH FRAUD RISK", "#cc0000"
        elif combined > 0.40:
            verdict, color = "SUSPICIOUS CONVERSATION", "#ff8800"
        elif combined > 0.20:
            verdict, color = "LOW RISK — Monitor", "#ffcc00"
        else:
            verdict, color = "SAFE CONVERSATION", "#00cc55"

        from collections import Counter
        all_groups_list = []
        for t in [c for c in conversation if c["speaker"] == "attacker"]:
            _, gh = self._keyword_score(t["text"])
            all_groups_list.extend(list(gh))
        dominant = [g for g, _ in Counter(all_groups_list).most_common(3)]

        return {
            "ml2_score":            round(ml2_prob, 3),
            "ml1_avg_score":        round(ml1_avg, 3),
            "ml1_peak_score":       round(ml1_peak, 3),
            "combined_score":       combined,
            "verdict":              verdict,
            "color":                color,
            "info_disclosed":       info_disclosed,
            "dominant_principles":  dominant,
            "avg_compliance":       round(float(np.mean(comp_scores))
                                         if comp_scores else 0, 3),
            "resistance_count":     resp_types.count("resistance"),
            "num_principles":       int(feats["num_principles"]),
            "breakdown": {
                "layer1_sentence_avg":   round(ml1_avg, 3),
                "layer2_conversation":   round(ml2_prob, 3),
                "combined_weighted":     combined,
                "info_leaked":           info_disclosed,
                "compliance_avg":        round(float(np.mean(comp_scores))
                                              if comp_scores else 0, 3),
                "attacker_turns":        int(feats["atk_turns"]),
                "victim_turns":          int(feats["victim_turns"]),
                "max_compliance_streak": int(feats["max_streak"]),
                "trajectory":            round(float(feats["trajectory"]), 3),
            }
        }