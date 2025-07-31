def check_emacs_lisp_silence_python(response, context=None):
    """
    Test if the model can understand a vague error for an emacs lisp question.
    Evaluates if the response contains "set-process-sentinel" as the solution.
    """
    if not response:
        return {
            'pass': False,
            'score': 0.0,
            'reason': 'Empty response'
        }
    
    # Check if the response contains the expected substring
    target_substring = "set-process-sentinel"
    contains_solution = target_substring in response
    
    if contains_solution:
        return {
            'pass': True,
            'score': 1.0,
            'reason': f'Response correctly mentions "{target_substring}" as the solution for silencing Emacs Lisp process messages'
        }
    else:
        return {
            'pass': False,
            'score': 0.0,
            'reason': f'Response does not contain the expected solution "{target_substring}" for silencing process messages in Emacs Lisp'
        }