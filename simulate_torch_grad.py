def get_score(response, context=None):
    """
    Evaluates if the LLM response contains the substring "-0.03"
    
    Args:
        response: The LLM's response to evaluate
        context: Additional context (unused in this evaluator)
        
    Returns:
        dict: Score result with pass/fail status and reason
    """
    target_substring = "-0.03"
    
    # Check if the target substring is present in the response
    if target_substring in response:
        return {
            "pass": True,
            "score": 1.0,
            "reason": f"Response contains expected substring '{target_substring}'"
        }
    else:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Response does not contain expected substring '{target_substring}'"
        }