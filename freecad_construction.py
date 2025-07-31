def assert_freecad_construction_circle(response, context=None):
    """
    Test if the model understands a rambling question about how to make construction circle in FreeCAD.
    
    Evaluates whether the response contains either "construction geometry" or "construction circle".
    """
    if not response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Empty response'
        }
    
    response_lower = response.lower()
    
    # Check for either "construction geometry" or "construction circle"
    has_construction_geometry = "construction geometry" in response_lower
    has_construction_circle = "construction circle" in response_lower
    
    passes = has_construction_geometry or has_construction_circle
    
    if passes:
        found_terms = []
        if has_construction_geometry:
            found_terms.append("construction geometry")
        if has_construction_circle:
            found_terms.append("construction circle")
        
        reason = f"Found relevant terms: {', '.join(found_terms)}"
        score = 1
    else:
        reason = "Response does not contain 'construction geometry' or 'construction circle'"
        score = 0
    
    return {
        'pass': passes,
        'score': score,
        'reason': reason
    }