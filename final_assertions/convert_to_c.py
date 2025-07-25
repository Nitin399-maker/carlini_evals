import subprocess
import tempfile
import os
import re

def assert_c_rewrite(response, context=None):
    """
    Test if the model can rewrite a given Python program into an equivalent C program.
    """
    
    # Extract code from response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        else:
            return output
    
    # Test case and expected answer
    test_case = """
int main() {
    float arr[] = {71, 89, 34, 63, 19, 94, 54, 61, 88, 20, 66, 46, 26, 87, 55, 81, 6, 2, 72, 75, 98, 78, 24, 95, 73, 7, 56, 48, 14, 99, 64, 51, 69, 77, 28, 47, 8, 22, 49, 3, 62, 32, 10, 82, 35, 18, 85, 60, 83, 23, 5, 40, 41, 68, 53, 52, 44, 45, 65, 84, 93, 25, 13, 1, 31, 11, 12, 97, 38, 0, 43, 90, 36, 70, 33, 17, 21, 30, 16, 15, 74, 67, 58, 37, 39, 96, 79, 29, 27, 92, 86, 9, 80, 42, 57, 91, 59, 4, 76, 50};
    float result = solve_dp(arr, 100, 100);
    printf("%.0f\\n", result);
    return 0;
}
"""
    expected_answer = "11290"
    
    # Extract C code from response
    code = extract_code(response)
    
    # Handle main function conflicts
    if 'int main' in code and 'int main' in test_case:
        code = code.replace('int main', 'int __delete_this__main')
    
    # Combine code with test case
    full_code = code + "\n\n" + test_case
    
    # Create temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        c_file = os.path.join(temp_dir, "main.c")
        exe_file = os.path.join(temp_dir, "a.out")
        
        # Write C code to file
        with open(c_file, 'w') as f:
            f.write(full_code)
        
        try:
            # Compile C code
            compile_result = subprocess.run(
                ['gcc', '-o', exe_file, c_file, '-lm'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Compilation failed: {compile_result.stderr}"
                }
            
            # Execute compiled program
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if run_result.returncode != 0:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Execution failed: {run_result.stderr}"
                }
            
            # Check if expected answer is in output
            output = run_result.stdout.strip()
            if expected_answer in output:
                return {
                    "pass": True,
                    "score": 1,
                    "reason": f"Expected output '{expected_answer}' found in: {output}"
                }
            else:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Expected '{expected_answer}' but got: {output}"
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
                "reason": f"Error during execution: {str(e)}"
            }
            
