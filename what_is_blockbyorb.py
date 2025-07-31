def assert_blocked_by_orb_explanation(response, context=None):
    """
    Test if the model knows what ERR_BLOCKED_BY_ORB means.
    Evaluates if the response contains "opaque resource blocking" (case-insensitive).
    """
    if not response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Response is empty or None'
        }
    
    target_substring = "opaque resource blocking"
    
    # Case-insensitive substring check
    if target_substring.lower() in response.lower():
        return {
            'pass': True,
            'score': 1,
            'reason': f'Response contains "{target_substring}"'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Response does not contain "{target_substring}"'
        }