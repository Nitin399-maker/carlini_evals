import subprocess
import re
import tempfile
import os
import sys

def assert_python_hello_world(response, context=None):
    """
    Evaluates if the LLM response contains Python code that prints "hello world"
    """
    try:
        # Extract code from response
        code = extract_code_with_main(response)
        # Run the Python code
        output = run_python_code(code)
        # Check if output contains "hello world"
        expected = "hello world"
        if expected in output.lower():
            return {
                'pass': True,
                'score': 1.0,
                'reason': f'Code successfully prints "{expected}"'
            }
        else:
            return {
                'pass': False,
                'score': 0.0,
                'reason': f'Code output "{output.strip()}" does not contain "{expected}"'
            }
    except Exception as e:
        return {
            'pass': False,
            'score': 0.0,
            'reason': f'Error: {str(e)}'
        }

def extract_code_with_main(response):
    """
    Extract code from response and ensure it's complete with main
    """
    # Clean up markdown code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    # Extract code from markdown blocks
    if "```" in response and response.count("```") >= 2:
        code = response.split("```")[1]
    else:
        code = response
        
    # If code doesn't have print statement, try to find it in the response
    if "print" not in code.lower():
        # Look for print statements in the full response
        lines = response.split('\n')
        code_lines = []
        for line in lines:
            if 'print(' in line or 'print "' in line:
                code_lines.append(line.strip())
        if code_lines:
            code = '\n'.join(code_lines)
            
    # Ensure the code is executable - add basic structure if needed
    if 'print' in code.lower() and 'def ' not in code and 'if __name__' not in code:
        # Code looks like a simple print statement, keep as is
        return code.strip()
    return code.strip()

def get_python_command():
    """
    Determine the correct Python command to use
    """
    # Try different Python commands
    commands = ['python', 'python3', 'py']
    
    for cmd in commands:
        try:
            # Try to run Python with the command
            subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return cmd
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
            
    # If we get here, try to use sys.executable
    if sys.executable:
        return sys.executable
        
    raise Exception("No Python interpreter found. Please ensure Python is installed and in PATH.")

def run_python_code(code):
    """
    Run Python code using subprocess and return output
    """
    # Get the appropriate Python command
    python_cmd = get_python_command()
    
    # Create temporary file with proper encoding
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        # Add encoding declaration
        f.write("# -*- coding: utf-8 -*-\n")
        f.write(code)
        temp_file = f.name
        
    try:
        # Run the Python code
        result = subprocess.run(
            [python_cmd, temp_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"Python execution failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        raise Exception("Code execution timed out")
    except Exception as e:
        raise Exception(f"Error running Python code: {str(e)}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except:
            pass  # Ignore cleanup errors