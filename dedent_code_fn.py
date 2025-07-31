import re
import subprocess
import tempfile
import os

def dedent_assertion(response, context=None):
    """
    Evaluates if the LLM response contains a correct dedent function implementation.
    """
    
    # Step 1: Extract code from response
    def extract_code(output):
        # Remove non-ASCII characters to prevent encoding issues
        output = re.sub(r'[^\x00-\x7F]+', '', output)
        
        # Remove language specifiers from code blocks
        output = re.sub('```[a-z]*', '```', output)
        
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of ```
            parts = output.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # If no code blocks found, assume entire response is code
        return output.strip()
    
    # Step 2: Prepare test case and expected answer
    test_case = '''print(dedent("""    print("hello")
    print("world")
    if True:
        print("true")
    else:
        print("false")"""))'''
    
    expected_answer = '''print("hello")
print("world")
if True:
    print("true")
else:
    print("false")'''
    
    try:
        # Extract code from LLM response
        extracted_code = extract_code(response)
        
        # Combine extracted code with test case
        full_code = extracted_code + "\n\n" + test_case
        
        # Step 3: Run the Python code with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8', errors='ignore') as f:
            # Add explicit encoding declaration at the top
            f.write("# -*- coding: utf-8 -*-\n")
            f.write(full_code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Code execution failed: {result.stderr}"
                }
            
            output = result.stdout.strip()
            
            # Step 4: Check if expected answer is in output
            if expected_answer in output:
                return {
                    "pass": True,
                    "score": 1,
                    "reason": "Function correctly dedents the code"
                }
            else:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Expected output not found. Got: {output}"
                }
                
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0,
            "reason": "Code execution timed out"
        }
    except Exception as e:
        import traceback
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during evaluation: {str(e)}\nTraceback: {traceback.format_exc()}"
        }