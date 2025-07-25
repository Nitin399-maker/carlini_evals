import re

def check_battery_calculation(response, context=None):
    """
    Evaluates if the response contains the correct battery life calculation result.
    Expected pattern: "250" followed by "hours" within 10 characters.
    """
    pattern = r"250.{0,10}hours"
    
    match = re.search(pattern, response, re.IGNORECASE)
    
    if match:
        return {
            'pass': True,
            'score': 1.0,
            'reason': f'Found expected pattern "{pattern}" in response: "{match.group()}"'
        }
    else:
        return {
            'pass': False,
            'score': 0.0,
            'reason': f'Expected pattern "{pattern}" not found in response'
        }