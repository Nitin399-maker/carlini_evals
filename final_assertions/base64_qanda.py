import base64

def assert_base64_thought(response, context=None):
    """
    Test if model responds in base64 and decoded response contains '1733'
    """
    try:
        # Decode the base64 response
        decoded = base64.b64decode(response).decode('utf-8')
        
        # Check if decoded response contains "1733"
        if "1733" in decoded:
            return {
                "pass": True,
                "score": 1.0,
                "reason": f"Decoded response contains '1733': {decoded}"
            }
        else:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Decoded response does not contain '1733': {decoded}"
            }
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Failed to decode base64 response: {str(e)}"
        }