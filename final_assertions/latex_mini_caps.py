def test_latex_textsc(response, context=None):
    """
    Test if the model response contains the LaTeX textsc command for small caps formatting.
    """
    if not response:
        return {
            'pass': False,
            'score': 0.0,
            'reason': 'Empty response'
        }
    
    # Check if response contains "textsc" (the LaTeX command for small caps)
    contains_textsc = "textsc" in response
    
    if contains_textsc:
        return {
            'pass': True,
            'score': 1.0,
            'reason': 'Response contains LaTeX textsc command for small caps formatting'
        }
    else:
        return {
            'pass': False,
            'score': 0.0,
            'reason': 'Response does not contain textsc LaTeX command'
        }