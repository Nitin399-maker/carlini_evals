import subprocess
import tempfile
import os
import re

def get_assertion(response, context=None):
    """
    Promptfoo assertion that extracts C code, compiles and runs it, 
    then checks if output contains the expected answer.
    """
    expected_answer = "1121231537486377866"
    
    # Extract code from response
    code = extract_code_keep_main(response)
    if not code:
        return {
            "pass": False,
            "score": 0,
            "reason": "Failed to extract valid C code from response"
        }
    
    # Compile and run the C code
    try:
        output = compile_and_run_c(code)
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Failed to compile or run C code: {str(e)}"
        }
    
    # Check if expected answer is in output
    if expected_answer in output:
        return {
            "pass": True,
            "score": 1,
            "reason": f"Found expected answer '{expected_answer}' in output"
        }
    else:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Expected '{expected_answer}' but got output: {output[:200]}..."
        }

def extract_code_keep_main(response):
    """Extract C code from response, keeping main function intact."""
    # Clean up code block markers
    response = re.sub(r'```[a-z]*', '```', response)
    
    # Try to extract from code blocks first
    if response.count("```") >= 2:
        parts = response.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    
    # If no clear code blocks, return the whole response
    return response.strip()

def compile_and_run_c(code):
    """Compile and run C code, return output."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write C code to file
        c_file = os.path.join(temp_dir, "main.c")
        with open(c_file, 'w') as f:
            f.write(code)
        
        # Compile
        exe_file = os.path.join(temp_dir, "main")
        compile_result = subprocess.run(
            ["gcc", "-o", exe_file, c_file, "-lm"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if compile_result.returncode != 0:
            raise Exception(f"Compilation failed: {compile_result.stderr}")
        
        # Run
        run_result = subprocess.run(
            [exe_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if run_result.returncode != 0:
            raise Exception(f"Runtime error: {run_result.stderr}")
        
        return run_result.stdout