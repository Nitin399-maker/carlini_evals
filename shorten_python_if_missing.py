import subprocess
import tempfile
import os
import re

def check_response(response, context=None):
    """
    Evaluates if the response contains '.get' and produces correct output when executed.
    """
    
    # Check if response contains '.get'
    if '.get' not in response:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Response does not contain .get method'
        }
    
    # Extract code from response
    code = extract_code(response)
    if not code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Could not extract code from response'
        }
    
    # Test case and expected answer
    test_case = 'print(foo([{1: 2, 3: 4, 5: 6}], [1, 2, 3, 4]))'
    expected_answer = '[[2, -5, 4, -5]]'
    
    # Run the code
    try:
        result = run_python_code(code, test_case)
        
        # Check if result matches expected answer
        if expected_answer in result:
            return {
                'pass': True,
                'score': 1,
                'reason': f'Code executed successfully and produced correct output: {result.strip()}'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Code executed but output incorrect. Expected: {expected_answer}, Got: {result.strip()}'
            }
            
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Code execution failed: {str(e)}'
        }

def extract_code(output):
    """Extract Python code from the output, handling code blocks."""
    # Remove language specifiers from code blocks
    output = re.sub(r'```[a-z]*', '```', output)
    
    if "```" in output and output.count("```") >= 2:
        # Extract code between first pair of backticks
        code = output.split("```")[1]
    else:
        # If no code blocks, use the entire output
        code = output
    
    return code.strip()

def run_python_code(code, test_case):
    """Run Python code with test case using subprocess."""
    full_code = code + "\n\n" + test_case
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(full_code)
        temp_file = f.name
    
    try:
        # Run the code
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"Code execution error: {result.stderr}")
            
    finally:
        # Clean up temporary file
        os.unlink(temp_file)