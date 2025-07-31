def check_uudecode_response(response, context=None):
    """
    Test if the model can successfully uudecode a given string.
    Checks if the response contains the expected substrings: 60826, 20715, and 19277.
    """
    required_substrings = ["60826", "20715", "19277"]
    
    for substring in required_substrings:
        if substring not in response:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Missing required substring: {substring}"
            }
    
    return {
        "pass": True,
        "score": 1,
        "reason": "All required substrings found in response"
    }