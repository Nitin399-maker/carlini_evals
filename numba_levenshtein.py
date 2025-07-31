import subprocess
import tempfile
import os
import re
import numpy as np

def get_assertion(response, context=None):
    """
    Evaluates if the response contains a valid numba implementation of Levenshtein distance.
    """
    
    # Step 1: Extract code from response
    def extract_code(output, keep_main=False):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of ```
            parts = output.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        # If no code blocks found, return the whole output
        return output.strip()
    
    # Mock Numba environment setup
    mock_environment = """
import numpy as np

# Mock numba decorator
def njit(*args, **kwargs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    return decorator

def jit(*args, **kwargs):
    return njit(*args, **kwargs)

# Make numba module with decorators
class Numba:
    def __init__(self):
        self.njit = njit
        self.jit = jit

numba = Numba()
from_numba = lambda x: x
"""
    
    extracted_code = extract_code(response)
    
    # Step 2: Check for numba imports
    has_numba_import = ("from numba" in extracted_code or "import numba" in extracted_code)
    
    # Step 3: Check for nopython mode
    has_nopython = ("nopython" in extracted_code or "njit" in extracted_code)
    
    if not (has_numba_import and has_nopython):
        return {
            "pass": False,
            "score": 0,
            "reason": f"Missing requirements - numba import: {has_numba_import}, nopython mode: {has_nopython}"
        }
    
    # Remove original numba imports
    code_lines = extracted_code.split('\n')
    cleaned_lines = []
    for line in code_lines:
        if not any(x in line for x in ['import numba', 'from numba']):
            cleaned_lines.append(line)
    cleaned_code = '\n'.join(cleaned_lines)
    
    # Step 4: Prepare test case
    test_case = """
# Test cases
test_cases = [
    (np.array([3, 5, 2, 4, 8, 7]), np.array([3, 4, 2, 4, 8, 7, 9]), 3),
    (np.array([1, 2, 3]), np.array([2, 3, 4]), 3),
    (np.array([1, 2, 3, 4]), np.array([1, 2, 3, 4]), 0),
    (np.array([]), np.array([1, 2]), 2),
]

# Run tests
for i, (seq1, seq2, expected) in enumerate(test_cases):
    result = levenshtein(seq1, seq2)
    print(f"Test {i+1} result:", result)
    if result != expected:
        print(f"Test {i+1} failed: expected {expected}, got {result}")
"""
    
    # Step 5: Run the code with test case
    full_code = mock_environment + "\n\n" + cleaned_code + "\n\n" + test_case
    
    try:
        # Create a temporary file with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(full_code)
            temp_file = f.name
        
        # Run the code with UTF-8 encoding
        result = subprocess.run(
            ["python", temp_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )
        
        # Clean up
        os.unlink(temp_file)
        
        if result.returncode != 0:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Code execution failed: {result.stderr}"
            }
        
        # Step 6: Check results
        output = result.stdout.strip()
        
        # Check if any tests failed
        if "failed" in output.lower():
            return {
                "pass": False,
                "score": 0,
                "reason": f"Some tests failed: {output}"
            }
        
        # Check if first test case result is correct
        if "Test 1 result: 3" in output:
            return {
                "pass": True,
                "score": 1,
                "reason": "All tests passed successfully"
            }
        
        return {
            "pass": False,
            "score": 0.5,
            "reason": f"Unexpected output format: {output}"
        }
            
    except subprocess.TimeoutExpired:
        if 'temp_file' in locals():
            os.unlink(temp_file)
        return {
            "pass": False,
            "score": 0,
            "reason": "Code execution timed out"
        }
    except Exception as e:
        if 'temp_file' in locals():
            os.unlink(temp_file)
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during execution: {str(e)}"
        }