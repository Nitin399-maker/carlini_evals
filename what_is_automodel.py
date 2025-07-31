def check_automodel_response(response, context=None):
    """
    Test if the model can interpret vague questions and will respond with the answer I want, 
    not the answer that's easy to find.
    
    Evaluates if the response contains "AutoModelForCausalLM" as the recommended solution.
    """
    if not response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Empty response'
        }
    
    # Check if response contains the expected substring
    target_substring = "AutoModelForCausalLM"
    contains_target = target_substring in response
    
    return {
        'pass': contains_target,
        'score': 1 if contains_target else 0,
        'reason': f'Response {"contains" if contains_target else "does not contain"} "{target_substring}"'
    }