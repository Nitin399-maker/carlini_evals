import re
import subprocess
import tempfile
import os

def assert_c_rewrite(response, context=None):
    """
    Evaluates if the LLM response contains valid C code that implements my_sqrt correctly.
    """
    
    # Extract code from response
    def extract_code(output):
        # Remove unicode characters that might cause encoding issues
        output = re.sub(r'[^\x00-\x7F]+', '', output)  # Remove non-ASCII characters
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        else:
            return output
    
    # Get the code
    code = extract_code(response)
    
    # Prepare test case
    test_case = """
int main() {
    printf("%d\\n", (int)(my_sqrt(12345, .001)*10));
    return 0;
}
"""
    
    # Handle main function conflicts
    if 'int main' in code and 'int main' in test_case:
        code = code.replace('int main', 'int __delete_this__main')
    
    # Add necessary headers if not present
    if '#include' not in code:
        code = '#include <stdio.h>\n#include <math.h>\n' + code
    
    # Combine code with test case
    full_code = code + "\n\n" + test_case
    
    try:
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            c_file = os.path.join(temp_dir, "main.c")
            exe_file = os.path.join(temp_dir, "a.out")
            
            # Write C code to file
            with open(c_file, 'w') as f:
                f.write(full_code)
            
            # Compile
            compile_result = subprocess.run(
                ['gcc', '-o', exe_file, c_file, '-lm'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f"Compilation failed: {compile_result.stderr}"
                }
            
            # Run the executable
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if run_result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f"Runtime error: {run_result.stderr}"
                }
            
            # Check if output contains expected result
            output = run_result.stdout.strip()
            expected = "1111"
            
            if expected in output:
                return {
                    'pass': True,
                    'score': 1,
                    'reason': f"Correct output found: {output}"
                }
            else:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f"Expected '{expected}' in output, got: {output}"
                }
                
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': "Code execution timed out"
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f"Error during evaluation: {str(e)}"
        }