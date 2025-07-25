import subprocess
import tempfile
import os
import re

def check_cpp_dataflow_dsl(response, context=None):
    """
    Evaluates if the C++ code response correctly implements dataflow DSL classes
    that produce output 625 when running: Const(2) >> Square() >> Inc() >> Square() >> Square() >> Print()
    """
    
    def extract_code(text):
        """Extract C++ code from markdown or plain text"""
        # Remove language specifiers from code blocks
        text = re.sub(r'```[a-z]*', '```', text)
        
        if "```" in text and text.count("```") >= 2:
            # Extract from code block
            parts = text.split("```")
            if len(parts) >= 2:
                return parts[1].strip()
        
        # If no code blocks, return the whole response
        return text.strip()
    
    def run_cpp_code(code, test_case):
        """Compile and run C++ code with test case"""
        # If both code and test_case have main functions, remove main from code
        if 'int main' in code and 'int main' in test_case:
            code = code.replace('int main', 'int __delete_this__main')
        
        # Combine code with test case
        full_code = code + "\n\n" + test_case
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            cpp_file = os.path.join(temp_dir, "main.cpp")
            exe_file = os.path.join(temp_dir, "a.out")
            
            # Write code to file
            with open(cpp_file, 'w') as f:
                f.write(full_code)
            
            try:
                # Compile
                compile_result = subprocess.run(
                    ['g++', '-o', exe_file, cpp_file, '-lm'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if compile_result.returncode != 0:
                    return f"Compilation failed: {compile_result.stderr}"
                
                # Run
                run_result = subprocess.run(
                    [exe_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if run_result.returncode != 0:
                    return f"Runtime error: {run_result.stderr}"
                
                return run_result.stdout
                
            except subprocess.TimeoutExpired:
                return "Execution timed out"
            except Exception as e:
                return f"Error: {str(e)}"
    
    # Extract code from response
    extracted_code = extract_code(response)
    
    # Test case that should produce output 625
    test_case = """int main() {
Const(2) >> Square() >> Inc() >> Square() >> Square() >> Print();
return 0;
}"""
    
    # Run the code
    output = run_cpp_code(extracted_code, test_case)
    
    # Check if output contains "625"
    if isinstance(output, str) and "625" in output:
        return {
            "pass": True,
            "score": 1.0,
            "reason": f"Code successfully produced expected output containing '625'. Full output: {output.strip()}"
        }
    else:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Code did not produce expected output '625'. Got: {output}"
        }