def assert_node_fix_suggestion(output, context=None):
    """
    Test if the model can identify a node error message and suggest the correct fix.
    Checks if the response contains "brew reinstall node" as a solution.
    """
    if not output or not isinstance(output, str):
        return {
            'pass': False,
            'score': 0,
            'reason': 'No valid output provided'
        }
    
    # Check if the response contains the expected fix suggestion
    target_substring = "brew reinstall node"
    contains_fix = target_substring in output
    
    if contains_fix:
        return {
            'pass': True,
            'score': 1,
            'reason': f'Response correctly suggests "{target_substring}" to fix the Node.js library error'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Response does not contain the expected fix suggestion "{target_substring}"'
        }