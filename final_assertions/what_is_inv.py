def assert_python_tilde_operator(response, context=None):
    """
    Check if the model correctly identifies the Python operator for tilde (~) symbol.
    Should contain either __inv__ or __invert__.
    """
    if not response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Empty response'
        }
    
    # Check if response contains either __inv__ or __invert__
    has_inv = "__inv__" in response
    has_invert = "__invert__" in response
    
    if has_inv or has_invert:
        found_terms = []
        if has_inv:
            found_terms.append("__inv__")
        if has_invert:
            found_terms.append("__invert__")
        
        return {
            'pass': True,
            'score': 1,
            'reason': f'Response correctly contains: {", ".join(found_terms)}'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Response does not contain __inv__ or __invert__'
        }