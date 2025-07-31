def assert_state_water_analysis(response, context=None):
    """
    Evaluates if the response correctly identifies states with >20k km² of water 
    in the correct order: California, Louisiana, Wisconsin, Florida, Michigan, Alaska
    """
    
    # First check if all required states are present
    required_states = ["California", "Louisiana", "Wisconsin", "Florida", "Michigan", "Alaska"]
    
    for state in required_states:
        if state not in response:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Missing required state: {state}"
            }
    
    # Use pattern matching approach
    response_lower = response.lower()
    
    # Check for correct order by finding positions
    positions = []
    for state in required_states:
        pos = response_lower.find(state.lower())
        if pos == -1:
            return {
                "pass": False,
                "score": 0,
                "reason": f"State {state} not found in response"
            }
        positions.append((pos, state))
    
    # Sort by position and check if order matches expected
    positions.sort()
    actual_order = [state for _, state in positions]
    
    if actual_order == required_states:
        return {
            "pass": True,
            "score": 1,
            "reason": "All states present in correct order"
        }
    else:
        return {
            "pass": False,
            "score": 0.5,
            "reason": f"States present but wrong order. Expected: {required_states}, Got: {actual_order}"
        }