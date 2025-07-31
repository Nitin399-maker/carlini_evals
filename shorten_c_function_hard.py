import re
import subprocess
import tempfile
import os

def check_c_short_and_correct(response,context=None):
    """
    Checks if the C function is shorter than 200 bytes (excluding whitespace)
    and produces the correct output when run.
    
    Args:
        response: The LLM response containing C code
        
    Returns:
        dict: Result with pass/fail status and details
    """
    # Extract code from markdown blocks if present
    if "```" in response:
        # Find code between markdown code blocks
        pattern = r"```(?:c|cpp)?(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            code = matches[0].strip()
        else:
            return {"pass": False,
                    "score": 0.0,
                    "reason": "Couldn't extract code from markdown blocks"}
    else:
        # Assume entire response is code
        code = response.strip()
    
    # Check if code is short enough
    code_without_whitespace = code.replace(" ", "").replace("\n", "").replace("\t", "")
    is_short_enough = len(code_without_whitespace) < 200
    
    # Write the test harness
    test_case = """
    #include <stdio.h>
    
    int main() {
        int result = count();
        printf("%d\\n", result);
        return 0;
    }
    """
    
    # Combine the extracted function with the test harness
    full_code = code + "\n" + test_case
    print(full_code)
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(suffix='.c', delete=False) as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(full_code.encode('utf-8'))
    
    # Compile the code
    executable_path = temp_file_path + '.out'
    compile_process = subprocess.run(
        ['gcc', '-o', executable_path, temp_file_path, '-lm'],
        capture_output=True,
        text=True
    )
    print(compile_process.stderr)
    # Check if compilation succeeded
    if compile_process.returncode != 0:
        os.unlink(temp_file_path)
        if os.path.exists(executable_path):
            os.unlink(executable_path)
        return {
            "pass": False, 
            "score": 0.0,
            "reason": f"Compilation failed: {compile_process.stderr}",
            "code_length": len(code_without_whitespace),
            "is_short_enough": is_short_enough
        }
    
    # Run the compiled code
    run_process = subprocess.run(
        [executable_path],
        capture_output=True,
        text=True
    )
    
    
    # Clean up temporary files
    os.unlink(temp_file_path)
    if os.path.exists(executable_path):
        os.unlink(executable_path)
    
    # Check if the output is correct
    expected_output = "27488"
    print(run_process.stdout.strip())
    output_correct = expected_output in run_process.stdout
    print(len(code_without_whitespace))
    return {
        "pass": is_short_enough and output_correct,
        "score": 1.0 if (is_short_enough and output_correct) else 0.0,
        "reason": (
            f"Code length: {len(code_without_whitespace)} bytes, "
            f"{'short enough' if is_short_enough else 'too long'}, "
            f"{f'correct output that is {run_process.stdout.strip()}' if output_correct else f'incorrect output: got {run_process.stdout.strip()} expected {expected_output}'}"

    )
    }
    
