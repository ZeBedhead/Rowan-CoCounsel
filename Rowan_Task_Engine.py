from Rowan_Logic_Engine import evaluate_argument
from ReadingLaw_Engine import interpret_statute
from Specter_Response_Generator import specter_response_engine

def task_engine(payload: dict) -> dict:
    """
    Executes workflows based on mode and adaptive completeness rules with normalized scoring.
    Pacific Region update for clarity and uniform deployment.
    """

    mode = payload.get("mode", "analysis")
    user_input = payload.get("user_input", "")
    directive = payload.get("directive", {})
    needs = directive.get("execution_policy", {}).get("needs", [])

    # Initialize container
    results = {
        "mode": mode,
        "status": "in_progress",
        "logic_result": None,
        "canon_result": None,
        "recommendations": [],
        "persona_response": None,
        "weighting": {"logic": 0.5, "canon": 0.5}
    }

    # Dynamic Weighting by Mode
    if mode == "analysis":
        results["weighting"] = {"logic": 0.6, "canon": 0.4}
    elif mode == "adversarial":
        results["weighting"] = {"logic": 0.5, "canon": 0.5}
    elif mode == "strategy":
        results["weighting"] = {"logic": 0.4, "canon": 0.6}

    # Pull Logic Engine if needed
    if "logic" in needs:
        logic_raw = evaluate_argument(user_input)
        if logic_raw:
            results["logic_result"] = {
                "score": round(logic_raw.get("adjusted_score", 0), 3),
                "analysis": logic_raw.get("analysis"),
                "fallacies": logic_raw.get("fallacies", {}),
                "razors": logic_raw.get("razors", {})
            }

    # Pull ReadingLaw Engine if needed
    if "canon" in needs:
        canon_raw = interpret_statute(user_input, user_input, mode="json")
        if canon_raw:
            results["canon_result"] = {
                "score": round(canon_raw.get("score", 0), 3),
                "top_interpretation": canon_raw.get("top_interpretation"),
                "applied_canons": canon_raw.get("applied_canons", []),
                "warning": canon_raw.get("warning"),
                "alternatives": canon_raw.get("alternatives", [])
            }

    # Compute weighted score
    logic_score = results["logic_result"]["score"] if results["logic_result"] else 0
    canon_score = results["canon_result"]["score"] if results["canon_result"] else 0

    weighted_score = round(
        (logic_score * results["weighting"]["logic"]) +
        (canon_score * results["weighting"]["canon"]),
        3
    )

    # Mode-specific actions
    if mode == "analysis":
        results["status"] = "validated" if weighted_score >= 0.9 else "issues_detected"
        if results["status"] == "issues_detected":
            results["recommendations"].append("Tighten logical structure or reinforce statutory interpretation.")

    elif mode == "adversarial":
        results["status"] = "attack_report"
        if results["logic_result"]:
            fallacies = [f["fallacy"] for f in results["logic_result"].get("fallacies", {}).get("detected_fallacies", [])]
            if fallacies:
                results["recommendations"].append(f"Exploit these reasoning flaws: {', '.join(fallacies)}")
        if results["canon_result"] and results["canon_result"].get("warning"):
            results["recommendations"].append("Leverage canon conflicts or warnings for counterargument advantage.")

    elif mode == "strategy":
        results["status"] = "strategic_synthesis"
        results["recommendations"].append("Anchor persuasion in canons with highest interpretive weight.")
        if results["logic_result"]:
            results["recommendations"].append("Apply Occam and Hitchens razors to streamline complexity.")

    # Persona Feedback Layer
    results["persona_response"] = specter_response_engine(
        text=user_input,
        claim=f"{mode.upper()} MODE | Weighted Score: {weighted_score}",
        facts=[],
        rules=results["canon_result"].get("applied_canons", []) if results["canon_result"] else [],
        razors=[r.get("razor") for r in results["logic_result"].get("razors", {}).get("matched_razors", [])] if results["logic_result"] else [],
        fallacies=[f.get("fallacy") for f in results["logic_result"].get("fallacies", {}).get("detected_fallacies", [])] if results["logic_result"] else []
    )

    results["final_score"] = weighted_score
    results["status"] = "complete"
    return results
