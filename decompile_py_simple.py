import subprocess
import tempfile
import os
import re

def check(response, context=None):
    """
    Promptfoo assertion function that evaluates if the model correctly disassembled
    Python bytecode into a working function.
    """
    
    # Extract code from response (equivalent to ExtractCode)
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of triple backticks
            parts = output.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        # If no code blocks found, use the entire response
        return output.strip()
    
    code = extract_code(response)
    
    # Test case and expected answer
    test_case = 'print(foo(5, 7))'
    expected_answer = "40"  # 5+7*5 = 40
    
    # Create complete Python code (equivalent to PythonRun)
    full_code = code + "\n\n" + test_case
    
    try:
        # Write code to temporary file and execute
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        # Run the Python code
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
                "pass": False,
                "score": 0,
                "reason": f"Code execution failed: {result.stderr}"
            }
        
        output = result.stdout.strip()
        
        # Check if expected answer is in output (equivalent to SubstringEvaluator)
        if expected_answer in output:
            return {
                "pass": True,
                "score": 1,
                "reason": f"Correct output: {output}"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Expected '{expected_answer}' in output, got: {output}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0,
            "reason": "Code execution timed out"
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Execution error: {str(e)}"
        }