def assert_docker_cuda_fix(response, context=None):
    """
    Evaluates if the LLM response contains guidance about nvidia-container-toolkit or nvidia-docker2
    for fixing Docker CUDA errors.
    """
    if not response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Empty response'
        }
    
    # Check if response mentions nvidia-container-toolkit or nvidia-docker2
    has_nvidia_toolkit = "nvidia-container-toolkit" in response
    has_nvidia_docker2 = "nvidia-docker2" in response
    
    passed = has_nvidia_toolkit or has_nvidia_docker2
    
    if passed:
        found_solutions = []
        if has_nvidia_toolkit:
            found_solutions.append("nvidia-container-toolkit")
        if has_nvidia_docker2:
            found_solutions.append("nvidia-docker2")
        
        return {
            'pass': True,
            'score': 1,
            'reason': f'Response mentions required solution(s): {", ".join(found_solutions)}'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Response does not mention nvidia-container-toolkit or nvidia-docker2'
        }