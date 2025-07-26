from engines.Rowan_Intention_Engine import process_intention

def run_pipeline(user_input: str, mode: str = None, session_id: str = "default"):
    """
    Main orchestration entry point.
    Delegates to Rowan Intention Engine which calls Task Engine and other layers.
    """
    result = process_intention(user_input=user_input, mode=mode, session_id=session_id)
    return result
