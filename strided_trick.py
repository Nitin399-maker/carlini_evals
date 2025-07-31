import subprocess
import re
import tempfile
import os

def assert_strided_numpy(response, context=None):
    """
    Evaluates if the response contains a correct implementation of the strided trick function.
    """
    
    # Extract code from response
    def extract_code(output):
        # Remove non-ASCII characters to prevent encoding issues
        output = re.sub(r'[^\x00-\x7F]+', '', output)
        
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        else:
            return output
    
    code = extract_code(response)
    
    # Check if response contains "as_strided" (required for strided trick)
    if "as_strided" not in code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Code does not use as_strided function'
        }
    
    # Prepare test case
    test_case = """
import numpy as np
# Test the function
result_shape = strides(np.arange(100)).shape
result_sum = strides(np.arange(100)).sum()
print(f"Shape: {result_shape}")
print(f"Sum: {result_sum}")
"""
    
    # Combine code with test case
    full_code = code + "\n\n" + test_case
    
    # Write to temporary file and execute with UTF-8 encoding
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8', errors='ignore') as f:
            # Add encoding declaration
            f.write("# -*- coding: utf-8 -*-\n")
            f.write(full_code)
            temp_file = f.name
        
        # Run the code
        result = subprocess.run(
            ['python', temp_file], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        # Clean up
        os.unlink(temp_file)
        
        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Code execution failed: {result.stderr}'
            }
        
        output = result.stdout.strip()
        
        # Check for expected outputs
        expected_shape = "(6, 50)"
        expected_sum = "14850"
        
        shape_correct = expected_shape in output
        sum_correct = expected_sum in output
        
        if shape_correct and sum_correct:
            return {
                'pass': True,
                'score': 1,
                'reason': 'Function correctly implements strided trick with expected output'
            }
        elif shape_correct:
            return {
                'pass': False,
                'score': 0.5,
                'reason': 'Shape is correct but sum is incorrect'
            }
        elif sum_correct:
            return {
                'pass': False,
                'score': 0.5,
                'reason': 'Sum is correct but shape is incorrect'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Neither shape nor sum match expected values. Got output: {output}'
            }
            
    except subprocess.TimeoutExpired:
        if 'temp_file' in locals():
            os.unlink(temp_file)
        return {
            'pass': False,
            'score': 0,
            'reason': 'Code execution timed out'
        }
    except Exception as e:
        if 'temp_file' in locals():
            os.unlink(temp_file)
        import traceback
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error during execution: {str(e)}\nTraceback: {traceback.format_exc()}'
        }