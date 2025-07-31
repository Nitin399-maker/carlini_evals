def get_assert(response, context=None):
    """
    Evaluates if the response contains either '-o raw' or '-l ' substring.
    
    Args:
        response: The LLM response string
        context: Optional context (unused)
    
    Returns:
        dict: Contains 'pass' boolean and 'reason' string
    """
    if not isinstance(response, str):
        return {
            'pass': False,
            'reason': 'Response is not a string'
        }
    
    # Check for either '-o raw' or '-l ' in the response
    has_o_raw = '-o raw' in response
    has_l_flag = '-l ' in response
    
    if has_o_raw or has_l_flag:
        found_flags = []
        if has_o_raw:
            found_flags.append('-o raw')
        if has_l_flag:
            found_flags.append('-l ')
        
        return {
            'pass': True,
            'score': 1.0,
            'reason': f'Found required lpr flag(s): {", ".join(found_flags)}'
        }
    else:
        return {
            'pass': False,
            'score': 0.0,
            'reason': 'Response does not contain required lpr flags (-o raw or -l )'
        }