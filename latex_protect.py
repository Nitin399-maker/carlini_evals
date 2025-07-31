def get_score(response, context=None):
    """
    Test if a model can fix a latex newline error in a caption.
    Checks if the response contains '\\protect' as the solution.
    """
    if not response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Empty response'
        }
    
    # Check if response contains the expected substring "\\protect"
    if "\\protect" in response:
        return {
            'pass': True,
            'score': 1,
            'reason': 'Response correctly mentions \\protect for fixing latex newline in caption'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Response does not contain \\protect - missing the correct solution for latex caption newline error'
        }