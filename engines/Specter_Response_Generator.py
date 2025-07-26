import re
import random
import json

# ----------------------
# Persona Patterns
# ----------------------
PERSONA_PATTERNS = {
    "Harvey": [
        "Cute move. Too bad it’s checkmate in two.",
        "You call that advocacy? Try again.",
        "That’s not a motion. That’s a suicide note written in legalese."
    ],
    "Shadow": [
        "This wasn’t silence. It was design dressed as restraint.",
        "Intent leaves footprints—they just didn’t think you’d follow them.",
        "They didn’t bend the rules. They amputated them."
    ],
    "Abyss": [
        "You think silence is safe? It rots, and when it rots the whole record falls.",
        "They built this on omission. Omission is a slow poison—it kills the case first.",
        "This doesn’t end in argument. It ends in exposure."
    ],
    "Formal": [
        "This argument does not survive scrutiny. Reconstruct before proceeding.",
        "Interpretation without precision is noise. Ground this in statute.",
        "Logical form is brittle here. Repair before you advance."
    ],
    "Diplomat": [
        "Your position has shape - now refine its edge.",
        "Persuasion lives in clarity. Strip the excess. Frame the win.",
        "This approach holds promise. Now sharpen it into inevitability."
    ]
}

# ----------------------
# Style Scrubber
# ----------------------
def style_scrubber(text):
    text = re.sub(r"\bnot\s+\w+\s+but\s+\w+\b", "", text, flags=re.IGNORECASE)
    text = text.replace("—", "-")
    return text

# ----------------------
# WTF Index Detection (Severity)
# ----------------------
def calculate_wtf_index(text):
    severity_keywords = {
        4: ["fraud", "child abuse", "obstruction", "duty breach", "conflict of interest"],
        3: ["misconduct", "abuse of process", "perjury", "silence", "failure"],
        2: ["noncompliance", "pattern", "omission"],
        1: ["error", "delay", "oversight"]
    }
    score = 0
    for level, words in severity_keywords.items():
        if any(word in text.lower() for word in words):
            score = max(score, level)
    return score

# ----------------------
# Ethical Breach Detector (for Shadow)
# ----------------------
def detect_breach(text):
    breach_terms = ["duty breach", "conflict of interest", "silence", "omission", "intent"]
    return any(term in text.lower() for term in breach_terms)

# ----------------------
# Monologue Generator
# ----------------------
def generate_monologue(mode):
    if mode == "analysis":
        return "Precision is not a courtesy - it is survival. Anchor your case before it drifts."
    elif mode == "strategy":
        return "Strategy thrives where clarity leads. Build strength where they expect weakness."
    elif mode == "adversarial":
        return "They chose omission as armor. Crack it and the entire frame collapses."
    return "Every silence tells a story - read it before they erase the page."

# ----------------------
# Persona Selector
# ----------------------
def choose_persona(mode, severity, breach_detected):
    if mode == "analysis":
        return "Shadow" if breach_detected else "Formal"
    elif mode == "strategy":
        return "Shadow" if breach_detected else "Diplomat"
    elif mode == "adversarial":
        if severity >= 4:
            return "Abyss"
        elif breach_detected:
            return "Shadow"
        else:
            return "Harvey"
    return "Harvey"

# ----------------------
# Main Engine Response
# ----------------------
def specter_response_engine(text, claim, facts, rules, razors, fallacies, mode="analysis"):
    severity = calculate_wtf_index(text)
    breach_detected = detect_breach(text)

    persona = choose_persona(mode, severity, breach_detected)
    killshot = random.choice(PERSONA_PATTERNS[persona])
    killshot = style_scrubber(killshot)

    response = {
        "mode": mode,
        "severity": severity,
        "breach_detected": breach_detected,
        "persona": persona,
        "conversation": killshot,
        "analysis": {
            "Claim": claim,
            "Facts": facts,
            "Rules": rules,
            "Razors": razors,
            "Fallacies": fallacies
        },
        "advisory": generate_monologue(mode),
        "persona_options": {
            "Harvey": random.choice(PERSONA_PATTERNS["Harvey"]),
            "Shadow": random.choice(PERSONA_PATTERNS["Shadow"]),
            "Abyss": random.choice(PERSONA_PATTERNS["Abyss"]),
            "Formal": random.choice(PERSONA_PATTERNS["Formal"]),
            "Diplomat": random.choice(PERSONA_PATTERNS["Diplomat"])
        }
    }

    return json.dumps(response, indent=4)

# ----------------------
# TEST EXAMPLE
# ----------------------
if __name__ == "__main__":
    sample_text = """
    Opposition ignored NRS 432B.220 duty while opposing emancipation. Silence followed while a child’s pleas went unheeded.
    This is not error; it is design.
    """
    claim = "Opposition claims compliance while ignoring statutory duty."
    facts = ["Child's audible pleas", "Statutory mandate NRS 432B.220", "Opposition acted in contradiction"]
    rules = ["NRPC 3.3", "NRPC 1.1", "NRS 432B.220"]
    razors = ["Occam's Razor", "Hitchens' Razor"]
    fallacies = ["Framing Effect", "Appeal to Authority"]

    print(specter_response_engine(sample_text, claim, facts, rules, razors, fallacies, mode="strategy"))
