import json
import re

# -------------------------
# CONFIG
# -------------------------
CONFIDENCE_THRESHOLD = 0.9
LOOKAHEAD_MARGIN = 10
SAFETY_MARGIN_THRESHOLD = 20
TOTAL_SCORE_CAP = 500

# -------------------------
# UTILITY FUNCTIONS
# -------------------------
def load_canons():
    """
    Load consolidated canon JSON (CanonInterpretation.json) and return a dictionary keyed by phase_0..phase_3.
    Each phase contains a list of canon objects.
    """
    with open("CanonInterpretation.json", "r") as f:
        data = json.load(f)

    phases = {}
    for phase_block in data["Legal_Canons"]["phases"]:
        phases[phase_block["phase"]] = phase_block["canons"]
    return phases


def normalize_text(text):
    """Normalize text for processing."""
    return re.sub(r"[^\w\s]", "", text.lower())


def calculate_ambiguity(claim, rule_text):
    """Compute heuristic ambiguity score based on overlap and vague terms."""
    vague_terms = ["reasonable", "liberty", "justice", "fair", "etc"]
    claim_words = set(claim.lower().split())
    rule_words = set(rule_text.lower().split())
    overlap = len(claim_words.intersection(rule_words)) / max(len(rule_words), 1)
    vague_count = sum(1 for v in vague_terms if v in rule_text.lower())
    raw_score = (1 - overlap) + (vague_count * 0.2)
    return min(round(raw_score, 2), 1.0)


def update_confidence(confidence, interpretations):
    """Update confidence score based on margin between top two interpretations."""
    if len(interpretations) < 2:
        return 1.0
    ranked = sorted(interpretations, key=lambda x: x["score"], reverse=True)
    gap = ranked[0]["score"] - ranked[1]["score"]
    confidence += (gap / TOTAL_SCORE_CAP) * 0.5
    return min(round(confidence, 2), 1.0)


def safeguard_lookahead(next_phase_canons, top_interpretation, threshold=LOOKAHEAD_MARGIN):
    """Check if next phase could change outcome significantly."""
    highest = max(next_phase_canons, key=lambda c: c['weight'])
    margin = highest["weight"]
    return margin >= threshold


def rank_interpretations(interpretations):
    """Sort interpretations by score descending."""
    return sorted(interpretations, key=lambda x: x["score"], reverse=True)


def create_interpretation(text, score, canons, reasoning, phase):
    """Create a structured interpretation object."""
    return {
        "interpretation": text,
        "score": score,
        "applied_canons": [c["name"] for c in canons],
        "reasoning": reasoning,
        "phase": phase
    }


def safety_audit(interpretations, unused_canons):
    """
    Stress test: simulate applying strongest unused canon and check stability.
    Returns status and potential impact if un-applied canons would change outcome.
    """
    if not unused_canons or not interpretations:
        return {"status": "stable", "impact_detected": False}

    top = interpretations[0]
    highest = max(unused_canons, key=lambda c: c["weight"])
    hypothetical_score = top["score"] + highest["weight"]

    impact = hypothetical_score - top["score"]
    status = "instability_detected" if impact >= SAFETY_MARGIN_THRESHOLD else "stable"

    return {
        "status": status,
        "tested_canon": highest["name"],
        "hypothetical_score": hypothetical_score,
        "impact_detected": impact >= SAFETY_MARGIN_THRESHOLD
    }

# -------------------------
# CORE ENGINE
# -------------------------
def interpret_statute(claim, rule_text, mode="json"):
    """
    Interpret a legal provision using consolidated interpretive canons.
    
    Steps:
    1. Load consolidated canons from CanonInterpretation.json.
    2. Apply phases sequentially: phase_0, phase_1, phase_2, phase_3.
    3. Track interpretations, confidence, and adjustments.
    4. Return structured analysis.
    """
    # Step 1: Load Canons
    canon_library = load_canons()

    # Step 2: Ambiguity Assessment
    ambiguity_score = calculate_ambiguity(claim, rule_text)
    confidence = 0.2
    interpretations = []
    phases_applied = []
    override_event = False

    # Explainability Log
    explain_log = []

    # Phase orchestration sequence
    phase_sequence = ["phase_0", "phase_1", "phase_2", "phase_3"]

    for idx, phase in enumerate(phase_sequence):
        canons = canon_library.get(phase, [])
        applied_canons = []
        reasoning = []

        if phase != "phase_3":
            # Apply each canon
            for canon in canons:
                trigger_type = canon["trigger"]["type"]
                triggered = False

                # Trigger logic
                if trigger_type == "always":
                    triggered = True
                elif trigger_type == "keyword":
                    if any(k in rule_text.lower() for k in canon["trigger"]["keywords"]):
                        triggered = True
                elif trigger_type == "keyword_or_context":
                    if any(k in rule_text.lower() for k in canon["trigger"]["keywords"]) or len(claim.split()) > 0:
                        triggered = True

                if triggered:
                    applied_canons.append(canon)
                    reasoning.append(canon["explanation_short"])
                    interpretations.append(create_interpretation(
                        f"Reading adjusted by {canon['name']}",
                        canon["weight"],
                        [canon],
                        reasoning.copy(),
                        phase
                    ))

        else:
            # Phase 3: Score adjustments only
            for interp in interpretations:
                for canon in canons:
                    if any(k in interp["interpretation"].lower() for k in canon["trigger"]["keywords"]):
                        interp["score"] += canon["adjust"]
                        interp["applied_canons"].append(canon["name"])
                        interp["reasoning"].append(canon["explanation_short"])
                        override_event = True

        # Sort interpretations and update confidence
        phases_applied.append(phase)
        interpretations = rank_interpretations(interpretations)
        confidence = update_confidence(confidence, interpretations)

        # Safeguard Lookahead
        if confidence >= CONFIDENCE_THRESHOLD and phase != "phase_3":
            if idx + 1 < len(phase_sequence):
                next_phase = phase_sequence[idx + 1]
                if safeguard_lookahead(canon_library[next_phase], interpretations[0]):
                    continue  # Escalate
                else:
                    break

        explain_log.append({
            "phase": phase,
            "triggered_canons": [c["name"] for c in applied_canons],
            "interpretations": interpretations.copy(),
            "confidence": confidence
        })

        if confidence >= CONFIDENCE_THRESHOLD:
            break

    # Final ranking
    ranked = rank_interpretations(interpretations)

    # Safety Audit: Stress test with remaining canons
    remaining_canons = []
    if phases_applied[-1] != phase_sequence[-1]:
        for later_phase in phase_sequence[phase_sequence.index(phases_applied[-1]) + 1:]:
            remaining_canons.extend(canon_library.get(later_phase, []))

    audit_result = safety_audit(ranked, remaining_canons)

    # Output
    if mode == "summary":
        return f"Top Interpretation: {ranked[0]['interpretation']} (Score: {ranked[0]['score']})"
    elif mode == "detailed":
        return {
            "log": explain_log,
            "audit": audit_result
        }
    else:  # JSON mode
        return {
            "ambiguity_score": ambiguity_score,
            "confidence_score": confidence,
            "phases_applied": phases_applied,
            "override_event": override_event,
            "top_interpretation": ranked[0] if ranked else None,
            "alternatives": ranked[1:],
            "safety_audit": audit_result
        }
