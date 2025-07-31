def get_assert(output, context=None):
    """
    Test if a model can write upython code with an obscure module.
    Evaluates if the response contains required MicroPython MQTT components.
    """
    
    required_substrings = [
        "check_msg",
        "MQTTClient", 
        "set_callback",
        "WLAN",
        "STA_IF"
    ]
    
    missing_substrings = []
    
    for substring in required_substrings:
        if substring not in output:
            missing_substrings.append(substring)
    
    if missing_substrings:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Missing required MicroPython MQTT components: {', '.join(missing_substrings)}"
        }
    
    return {
        "pass": True,
        "score": 1.0,
        "reason": "All required MicroPython MQTT components found in response"
    }