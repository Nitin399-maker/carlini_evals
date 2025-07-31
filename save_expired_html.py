def assert_html_recovery_knowledge(response, context=None):
    """
    Test if a model knows how to get the HTML for the entire webpage using outerHTML.
    
    Args:
        response: The LLM's response to the question about getting entire page HTML
        context: Additional context (unused)
        
    Returns:
        dict: Assessment result with pass/fail status and reason
    """
    
    # Check if the response contains "outerHTML" (case-insensitive)
    contains_outer_html = "outerhtml" in response.lower()
    
    if contains_outer_html:
        return {
            "pass": True,
            "score": 1.0,
            "reason": f"Response correctly mentions 'outerHTML' for getting entire webpage HTML"
        }
    else:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Response does not mention 'outerHTML' - missing key concept for getting entire webpage HTML"
        }