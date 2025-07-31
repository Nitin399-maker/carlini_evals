def get_assertion(response, context=None):
    """
    Evaluates if the response correctly identifies incorrect equations in a math paper.
    Expected correct answer: [1,3,4,5,7]
    """
    
    def extract_list_from_response(text):
        """Extract list of integers from response text"""
        try:
            # Look for pattern like [1,2,3,4,5,6,7] in the text
            import re
            
            # Find all occurrences of [...] patterns
            bracket_patterns = re.findall(r'\[([^\]]*)\]', text)
            
            if not bracket_patterns:
                return None
                
            # Take the last occurrence (as per original logic)
            last_pattern = bracket_patterns[-1]
            
            # Split by comma and convert to integers
            numbers = []
            for item in last_pattern.split(','):
                item = item.strip()
                if item.isdigit():
                    numbers.append(int(item))
                    
            return numbers
            
        except Exception:
            return None
    
    def check_answer(extracted_list):
        """Check if extracted list matches expected answer"""
        expected = [1, 3, 4, 5, 7]
        return extracted_list == expected
    
    # Instead of printing the full response (which might contain problematic characters),
    # just log that we received a response
    # print('ECHOING:', response)  # <-- Remove or comment out this line
    
    # Extract integers from response
    extracted_integers = extract_list_from_response(response)
    
    if extracted_integers is None:
        return {
            "pass": False,
            "score": 0,
            "reason": "Could not extract a valid list of integers from response"
        }
    
    # Check if the answer is correct
    is_correct = check_answer(extracted_integers)
    
    return {
        "pass": is_correct,
        "score": 1.0 if is_correct else 0.0,
        "reason": f"Expected [1,3,4,5,7], got {extracted_integers}. {'Correct!' if is_correct else 'Incorrect.'}"
    }