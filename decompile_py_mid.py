import subprocess
import tempfile
import os
import re

def assert_disassemble_primes(response, context=None):
    """
    Promptfoo assertion that evaluates if the model can disassemble Python bytecode
    and create a function that returns a list of prime numbers and their negations.
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
    
    # Test case and expected answer
    test_case = """print(foo(20))"""
    expected_answer = "[2, 3, -3, 5, -5, 7, -7, 11, -11, 13, -13, 17, -17, 19, -19]"
    
    try:
        # Extract code from LLM response
        extracted_code = extract_code(response)
        
        # Create complete Python code
        full_code = extracted_code + "\n\n" + test_case
        
        # Write code to temporary file with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8', errors='ignore') as f:
            f.write(full_code)
            temp_file = f.name
        
        try:
            # Run Python code
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Code execution failed: {result.stderr}'
                }
            
            # Check if expected answer is in output
            output = result.stdout.strip()
            if expected_answer in output:
                return {
                    'pass': True,
                    'score': 1,
                    'reason': 'Successfully generated function that returns primes and their negations'
                }
            else:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Expected {expected_answer} but got: {output}'
                }
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Code execution timed out'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error during evaluation: {str(e)}'
        }