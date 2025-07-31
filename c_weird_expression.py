def assert_correct_c_expression(response, context=None):
    # Parse the response to extract content after "Final answer:"
    try:
        parsed_response = response.lower().split("final answer:")[-1].strip()
        
        # Define acceptable answers (case insensitive)
        acceptable_answers = ['*x+2', 'v+2']
        
        # Remove spaces and convert to lowercase for comparison
        cleaned_response = ''.join(parsed_response.split()).lower()
        
        # Check if any of the acceptable answers are in the cleaned response
        for answer in acceptable_answers:
            if answer.lower() in cleaned_response:
                return {
                    "pass": True,
                    "score": 1,
                    "reason": f"Found correct answer: {answer}"
                }
        
        return {
            "pass": False,
            "score": 0,
            "reason": f"Expected '*x+2' or 'v+2', but got: {parsed_response}"
        }
        
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error processing response: {str(e)}"
        }