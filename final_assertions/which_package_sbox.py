def check_sbox_package(response, context=None):
    """
    Checks if the model knows what latex package to import for the Sbox environment.
    Looks for 'fancybox' in the response.
    """
    if not response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Empty response'
        }
    
    # Check if 'fancybox' appears in the response
    if 'fancybox' in response:
        return {
            'pass': True,
            'score': 1,
            'reason': 'Response correctly mentions fancybox package'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Response does not mention fancybox package'
        }