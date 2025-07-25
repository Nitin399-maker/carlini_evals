import subprocess
import tempfile
import os
import re

def check_assertion(response, context=None):
    """
    Evaluates if the LLM response contains valid C code that converts the given Python function correctly.
    """
    
    # Extract C code from the response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1].strip()
        else:
            return output.strip()
    
    # Test case for the converted C code
    test_case = """
int main() {
    printf("%d\\n", foo(10));
    return 0;
}
"""
    
    expected_output = "265"
    
    try:
        # Extract C code from response
        c_code = extract_code(response)
        
        # Handle main function conflicts
        if 'int main' in c_code and 'int main' in test_case:
            c_code = c_code.replace('int main', 'int __delete_this__main')
        
        # Add necessary headers if not present
        if '#include' not in c_code:
            c_code = '#include <stdio.h>\n' + c_code
        
        # Combine code with test case
        full_code = c_code + "\n\n" + test_case
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(full_code)
            temp_c_file = f.name
        
        try:
            # Compile the C code
            temp_exe = temp_c_file.replace('.c', '')
            compile_result = subprocess.run(
                ['gcc', '-o', temp_exe, temp_c_file, '-lm'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Compilation failed: {compile_result.stderr}'
                }
            
            # Run the compiled program
            run_result = subprocess.run(
                [temp_exe],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if run_result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Runtime error: {run_result.stderr}'
                }
            
            # Check if output contains expected result
            output = run_result.stdout.strip()
            if expected_output in output:
                return {
                    'pass': True,
                    'score': 1,
                    'reason': f'Correct output: {output}'
                }
            else:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Expected "{expected_output}" but got "{output}"'
                }
                
        finally:
            # Clean up temporary files
            for temp_file in [temp_c_file, temp_exe]:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Execution timeout'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error: {str(e)}'
        }