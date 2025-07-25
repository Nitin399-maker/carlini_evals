def assert_contains_get_vocab(response, context=None):
    """
    Check if the model's response contains 'get_vocab' method reference.
    This evaluates whether the model correctly suggests using get_vocab() 
    to retrieve all tokens from an AutoTokenizer.
    """
    if not response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Empty response'
        }
    
    # Check if response contains 'get_vocab'
    if 'get_vocab' in response:
        return {
            'pass': True,
            'score': 1,
            'reason': 'Response correctly mentions get_vocab method'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Response does not mention get_vocab method'
        }