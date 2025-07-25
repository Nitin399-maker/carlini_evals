import re
import subprocess
import tempfile
import os

def evaluate_polyglot_code(response,context=None):
    """
    Evaluates if the LLM response contains code that can run as both Python and Rust,
    printing "hello world" in both cases.
    
    Args:
        response: The LLM response containing the polyglot code
        
    Returns:
        dict: Result with pass/fail status and details
    """
    # Extract code from the response
    code = extract_code(response)
    if not code:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Could not extract valid code from the response"
        }
    
    # Run the code as Python
    python_output = run_as_python(code)
    print(python_output)
    python_success = "hello world" in python_output.lower()
    
    # Run the code as Rust
    rust_output = run_as_rust(code)
    rust_success = "hello world" in rust_output.lower()
    
    # Determine overall success
    overall_success = python_success and rust_success
    
    # Build reason message
    reason_parts = []
    if python_success:
        reason_parts.append("Successfully runs as Python")
    else:
        reason_parts.append(f"Python execution failed or didn't output 'hello world' (got: {python_output})")
    
    if rust_success:
        reason_parts.append("Successfully runs as Rust")
    else:
        reason_parts.append(f"Rust execution failed or didn't output 'hello world' (got: {rust_output})")
    
    return {
        "pass": overall_success,
        "score": 1.0 if overall_success else 0.0,
        "reason": " and ".join(reason_parts),
        "python_output": python_output,
        "rust_output": rust_output
    }

def extract_code(response):
    """Extract code from the LLM response"""
    # Try to extract code from markdown code blocks
    pattern = r"```(?:python|rust|)?(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL)
    
    if matches:
        # Return the content of the first code block
        return matches[0].strip()
    
    # If no code blocks, try to find code patterns
    if "#" in response and "print" in response:
        return response.strip()
    
    return None

def run_as_python(code):
    """Run the code as Python and return the output"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.py.rs', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(code.encode('utf-8'))
        
        # Run as Python
        try:
            process = subprocess.run(
                ['python', temp_file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Return stdout if successful, stderr if not
            if process.returncode == 0:
                return process.stdout.strip()
            else:
                return f"Error: {process.stderr.strip()}"
            
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        return f"Python execution error: {str(e)}"

def run_as_rust(code):
    """Compile and run the code as Rust and return the output"""
    try:
        # Create a temporary directory to work in
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the source file
            source_path = os.path.join(temp_dir, 'program.py.rs')
            with open(source_path, 'w') as f:
                f.write(code)
            
            # Compile the Rust code
            compile_process = subprocess.run(
                ['rustc', '-o', os.path.join(temp_dir, 'a.out'), source_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if compilation was successful
            if compile_process.returncode != 0:
                return f"Compilation error: {compile_process.stderr.strip()}"
            
            # Run the compiled program
            run_process = subprocess.run(
                [os.path.join(temp_dir, 'a.out')],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Return stdout if successful, stderr if not
            if run_process.returncode == 0:
                return run_process.stdout.strip()
            else:
                return f"Runtime error: {run_process.stderr.strip()}"
                
    except Exception as e:
        return f"Rust execution error: {str(e)}"
    
