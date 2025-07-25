def get_assert(response, context=None):
    """
    Test if the model knows the LLAMA-2 70b hidden dimension size.
    Checks if response contains "8192" or "8,192".
    """
    if not response:
        return {
            "pass": False,
            "score": 0,
            "reason": "Empty response"
        }
    
    # Check if response contains either "8192" or "8,192"
    contains_8192 = "8192" in response
    contains_8192_comma = "8,192" in response
    
    # Return result in the expected format
    if contains_8192 or contains_8192_comma:
        return {
            "pass": True,
            "score": 1,
            "reason": "Response contains the correct hidden dimension size (8192)"
        }
    else:
        return {
            "pass": False,
            "score": 0,
            "reason": "Response does not contain the correct hidden dimension size (8192 or 8,192)"
        }