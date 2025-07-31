def assert_train_schedule_response(response, context=None):
    """
    Evaluates if the response contains both required substrings for the train schedule query.
    The response should contain "6:41" (arrival time) and "Millbrae" (transfer station).
    """
    if not response:
        return {
            'pass': False,
            'score': 0.0,
            'reason': 'Empty response'
        }
    
    # Check for required substrings
    has_time = "6:41" in response
    has_station = "Millbrae" in response
    
    # Both conditions must be true (AND operation)
    passed = has_time and has_station
    
    # Calculate score
    score = 1.0 if passed else 0.0
    
    # Generate reason
    missing_parts = []
    if not has_time:
        missing_parts.append("arrival time '6:41'")
    if not has_station:
        missing_parts.append("transfer station 'Millbrae'")
    
    if passed:
        reason = "Response correctly contains both required elements: arrival time and transfer station"
    else:
        reason = f"Response missing: {', '.join(missing_parts)}"
    
    return {
        'pass': passed,
        'score': score,
        'reason': reason
    }