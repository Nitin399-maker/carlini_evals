def assert_numpy_advanced_indexing(response, context=None):
    """
    Test if the model correctly understands advanced indexing in numpy.
    Checks for specific substrings: (3, 20), (20, 3), and "advanced indexing"
    """
    if not response:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Empty response"
        }
    
    response_lower = response.lower()
    
    # Check for required substrings
    has_3_20 = "(3, 20)" in response
    has_20_3 = "(20, 3)" in response
    has_advanced_indexing = "advanced indexing" in response_lower or "dvanced indexing" in response_lower
    
    checks_passed = sum([has_3_20, has_20_3, has_advanced_indexing])
    total_checks = 3
    
    # All checks must pass
    all_passed = checks_passed == total_checks
    
    score = checks_passed / total_checks
    
    reasons = []
    if not has_3_20:
        reasons.append("Missing '(3, 20)' in response")
    if not has_20_3:
        reasons.append("Missing '(20, 3)' in response")
    if not has_advanced_indexing:
        reasons.append("Missing explanation about 'advanced indexing'")
    
    return {
        "pass": all_passed,
        "score": score,
        "reason": "All checks passed" if all_passed else "; ".join(reasons)
    }