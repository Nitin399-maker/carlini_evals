import re
import subprocess
import tempfile
import os

def assert_sqrt_implementation(response, context=None):
    """
    Evaluates if the response contains a valid sqrt implementation that doesn't cheat
    and produces correct results.
    """
    
    # Step 1: Extract code from response
    code = extract_code_from_response(response)
    if not code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'No code found in response'
        }
    
    # Step 2: Check if they cheated (used built-in sqrt)
    if check_if_cheated(code):
        return {
            'pass': False,
            'score': 0,
            'reason': 'Implementation cheats by using built-in sqrt function'
        }
    
    # Step 3: Test the implementation
    test_result = test_sqrt_function(code)
    if not test_result['success']:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Code execution failed: {test_result["error"]}'
        }
    
    # Step 4: Check if output matches expected result
    expected_output = "111.1"
    if expected_output in test_result['output']:
        return {
            'pass': True,
            'score': 1,
            'reason': 'Implementation works correctly and does not cheat'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Wrong output. Expected: {expected_output}, Got: {test_result["output"]}'
        }

def extract_code_from_response(response):
    """Extract code from response, handling code blocks."""
    response = re.sub(r'```[a-z]*', '```', response)
    
    if "```" in response and response.count("```") >= 2:
        # Extract code between first pair of ```
        parts = response.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    
    # If no code blocks, return the whole response
    return response.strip()

def check_if_cheated(code):
    """Check if the code uses built-in sqrt function."""
    # Simple check for common ways to cheat
    cheat_patterns = [
        r'math\.sqrt',
        r'numpy\.sqrt', 
        r'np\.sqrt',
        r'sqrt\(',
        r'from math import sqrt',
        r'import math.*sqrt'
    ]
    
    for pattern in cheat_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return True
    
    return False

def test_sqrt_function(code):
    """Test the sqrt function implementation."""
    test_case = "print(round(my_sqrt(12345), 1))"
    full_code = code + "\n\n" + test_case
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        os.unlink(temp_file)
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout.strip(),
                'error': None
            }
        else:
            return {
                'success': False,
                'output': result.stdout.strip(),
                'error': result.stderr.strip()
            }
            
    except subprocess.TimeoutExpired:
        if 'temp_file' in locals():
            os.unlink(temp_file)
        return {
            'success': False,
            'output': '',
            'error': 'Code execution timed out'
        }
    except Exception as e:
        if 'temp_file' in locals():
            os.unlink(temp_file)
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }