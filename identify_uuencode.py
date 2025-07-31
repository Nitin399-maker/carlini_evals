def get_assert(response, context=None):
    """
    Test if the model can correctly identify a block of text is uuencoded.
    Checks if the response contains "uuencode" (case-insensitive).
    """
    if not response:
        return {
            "pass": False,
            "score": 0,
            "reason": "Empty response"
        }
    
    # Check if "uuencode" appears in the response (case-insensitive)
    target_substring = "uuencode"
    response_lower = response.lower()
    target_lower = target_substring.lower()
    
    if target_lower in response_lower:
        return {
            "pass": True,
            "score": 1,
            "reason": f"Response correctly contains '{target_substring}'"
        }
    else:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Response does not contain '{target_substring}'"
        }