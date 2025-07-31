def assert_float_format(response, context=None):
    """
    Checks if the response contains the correct f-string format for 3 decimal places.
    Expected substring: ":.3f}"
    """
    expected_substring = ":.3f}"
    
    if expected_substring in response:
        return {
            "pass": True,
            "score": 1.0,
            "reason": f"Response contains expected format string: '{expected_substring}'"
        }
    else:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Response does not contain expected format string: '{expected_substring}'"
        }