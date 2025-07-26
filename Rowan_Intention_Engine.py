# ----------------------
# GLOBAL SESSION CONTEXT
# ----------------------
SESSION_CONTEXT = {}

# ----------------------
# CLARITY-BASED AMBIGUITY SCORING
# ----------------------
def calculate_ambiguity_score(user_input: str) -> float:
    text = user_input.lower()
    tokens = text.split()
    score = 0

    # Short query is usually ambiguous
    if len(tokens) < 4:
        score += 0.5

    # Vague terms that kill clarity
    vague_terms = {"do", "make", "thing", "stuff", "handle", "help", "fix"}
    if any(term in tokens for term in vague_terms):
        score += 0.3

    # Missing domain-specific keywords
    domain_keywords = {"statute", "rule", "motion", "injunction", "file", "analyze", "draft", "simulate", "review"}
    if not any(k in tokens for k in domain_keywords):
        score += 0.3

    # Ambiguous question without constraints
    if "?" in text and len(tokens) < 8:
        score += 0.2

    return min(score, 1.0)

# ----------------------
# NEED-BASED CLARIFICATION PROMPTS
# ----------------------
def build_clarification_prompts(needs: list) -> list:
    prompts = []
    if "canon" in needs:
        prompts.append("Specify the statute, rule, or precedent relevant to your request.")
    if "logic" in needs:
        prompts.append("Clarify reasoning using connectors like 'if', 'then', or 'because'.")
    if "depth_analysis" in needs:
        prompts.append("Break down the question into smaller, focused parts.")
    if not prompts:
        prompts.append("Add missing details for clarity.")
    return prompts

# ----------------------
# CONTEXT-AWARE COMPLETENESS CHECK
# ----------------------
def determine_needs(user_input: str, logic_result: dict, mode: str = None):
    needs = []
    text = user_input.lower()

    if logic_result["adjusted_score"] < 0.8 or logic_result["fallacies"]["detected_fallacies"]:
        needs.append("logic")

    legal_keywords = ["statute", "rule", "canon", "precedent", "section", "motion"]
    if not any(k in text for k in legal_keywords):
        needs.append("canon")

    persuasive_razors = {"Hanlon's Razor", "Sagan's Standard", "Occam's Razor"}
    matched_razors = {r["razor"] for r in logic_result["razors"]["matched_razors"]}
    if matched_razors & persuasive_razors:
        needs.append("bias_control")

    if len(text.split()) > 60 or logic_result["status"] == "uncertain":
        needs.append("depth_analysis")

    return needs if needs else ["none"]

# ----------------------
# MAIN INTENTION ENGINE
# ----------------------
def process_intention(user_input: str, mode: str = None, session_id: str = "default"):
    context = SESSION_CONTEXT.get(session_id, {"attempts": 0})
    merged_input = user_input if not context.get("clarification_needed") else context["last_query"] + " " + user_input

    # STEP 1: Ambiguity Gate
    ambiguity_score = calculate_ambiguity_score(merged_input)
    if ambiguity_score >= 0.6:
        context.update({
            "last_query": merged_input,
            "clarification_needed": True,
            "attempts": context["attempts"] + 1
        })
        SESSION_CONTEXT[session_id] = context

        if context["attempts"] >= 3:
            return {
                "status": "failed",
                "reason": "Too many unclear attempts.",
                "clarity_score": ambiguity_score,
                "required": ["specific claim", "statutory reference", "desired action"],
                "feedback": "Cannot proceed without essential details."
            }

        dummy_logic_result = {"adjusted_score": 0, "status": "fail", "razors": {"matched_razors": []}, "fallacies": {"detected_fallacies": []}}
        needs = determine_needs(merged_input, dummy_logic_result, mode)
        return {
            "status": "clarification_needed",
            "clarity_score": ambiguity_score,
            "feedback": "Input lacks specificity.",
            "required": needs,
            "prompts": build_clarification_prompts(needs)
        }

    context.update({"clarification_needed": False, "attempts": 0})
    SESSION_CONTEXT[session_id] = context

    # STEP 2: Feasibility Gate
    tokens = merged_input.split()
    complexity_score = len(tokens) / 60
    if complexity_score > 1.0:
        return {
            "status": "proceed_with_warning",
            "reason": "Request is broad; may require multiple steps.",
            "feedback": f"Complexity score: {complexity_score:.2f}. Execution may need chunking."
        }

    # STEP 3: Mode Detection
    if not mode:
        mode = determine_mode(merged_input)

    # STEP 4: Logic Gate
    try:
        logic_result = evaluate_argument(merged_input)
    except Exception as e:
        return {"status": "logic_error", "error": str(e)}

    adjusted_score = logic_result["adjusted_score"]
    if adjusted_score < 0.71:
        if adjusted_score >= 0.5:
            status = "proceed_with_warning"
            warning = "Logic weak. Proceed cautiously."
        else:
            status = "blocked"
            warning = "Logic foundation too weak."
    else:
        status, warning = "processed", None

    # STEP 5: Completeness Check
    needs = determine_needs(merged_input, logic_result, mode)
    meta_directive = {"mode": mode, "execution_policy": {"mode": mode, "needs": needs}}

    # STEP 6: Inverse Razor Reasoning (Adversarial Mode)
    inverse_razors = []
    if mode in ["adversarial", "argument_testing"]:
        for razor in logic_result["razors"]["matched_razors"]:
            inverse_razors.append({
                "razor": razor["razor"],
                "counter": next((r["inverse"]["principle"] for r in RAZORS["Philosophical_Razors"]["razors"] if r["name"] == razor["razor"]), "")
            })

    # STEP 7: Task Engine Handoff
    try:
        task_payload = {"mode": mode, "user_input": merged_input, "directive": meta_directive}
        task_result = task_engine(task_payload)
    except Exception as e:
        return {"status": "task_engine_error", "error": str(e)}

    return {
        "status": status,
        "mode": mode,
        "clarity_score": 1.0 - ambiguity_score,
        "logic_evaluation": {
            "status": logic_result["status"],
            "logic_score": logic_result["logic"]["logic_score"],
            "adjusted_score": adjusted_score,
            "razor_bonus": logic_result["modifiers"]["razor_bonus"],
            "fallacy_penalty": logic_result["modifiers"]["fallacy_penalty"],
            "detected_razors": logic_result["razors"]["matched_razors"],
            "detected_fallacies": logic_result["fallacies"]["detected_fallacies"],
            "explanations": logic_result["explanations"]
        },
        "inverse_razors": inverse_razors if inverse_razors else None,
        "meta_directive": meta_directive,
        "handoff": task_result,
        "prompts": build_clarification_prompts(needs),
        "warning": warning
    }

# ----------------------
# TEST EXAMPLE
# ----------------------
if __name__ == "__main__":
    from Rowan_Logic_Engine import evaluate_argument, RAZORS
    from Rowan_Task_Engine import task_engine
    from Rowan_Mode_Engine import determine_mode
    user_input = "This is a test input." # Placeholder for actual user input
    mode = None
    session_id = "default"
    result = process_intention(user_input, mode, session_id)
    print(result)

#