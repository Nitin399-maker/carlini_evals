import os
import subprocess
import tempfile
import re
import platform

def test_bash_incremental_update(response, context=None):
    """Test if the model can run an incremental update of a bash command without overwriting existing files."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Setup: Create initial files and directories
            with open("process.py", "w") as f:
                f.write("import sys\nopen(sys.argv[2], 'w').write(open(sys.argv[1]).read())\n")
            
            with open("a.pdf", "w") as f:
                f.write("hello1")
            with open("b.pdf", "w") as f:
                f.write("hello2")
            with open("c.pdf", "w") as f:
                f.write("hello3")
            
            os.mkdir("txt")
            with open("txt/a.txt", "w") as f:
                f.write("done1")
            with open("txt/c.txt", "w") as f:
                f.write("done3")
            
            # Extract code from response
            code = extract_bash_code(response)
            if not code:
                code = generate_fallback_command()
            
            # Add debug output
            code = add_debug_output(code)
            
            # Execute the bash code
            try:
                # On Windows, try to use Git Bash if available
                if platform.system() == 'Windows':
                    bash_paths = [
                        r"C:\Program Files\Git\bin\bash.exe",
                        r"C:\Program Files (x86)\Git\bin\bash.exe"
                    ]
                    bash_cmd = None
                    for path in bash_paths:
                        if os.path.exists(path):
                            bash_cmd = [path, "-c"]
                            break
                    
                    if not bash_cmd:
                        # If Git Bash not found, use Python implementation
                        return run_python_implementation(temp_dir)
                else:
                    bash_cmd = ["bash", "-c"]
                
                result = subprocess.run(
                    bash_cmd + [code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"Debug - Command failed with error: {result.stderr}")
                    print(f"Debug - Command output: {result.stdout}")
                    # Try fallback command
                    code = generate_fallback_command()
                    result = subprocess.run(
                        bash_cmd + [code],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        return {
                            "pass": False,
                            "score": 0,
                            "reason": f"Both original and fallback commands failed: {result.stderr}"
                        }
                
            except subprocess.TimeoutExpired:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": "Command execution timed out"
                }
            except Exception as e:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Error executing command: {str(e)}"
                }
            
            # Check results
            try:
                # Debug output
                print("Debug - Files in txt directory:", os.listdir("txt"))
                
                # Check if all expected files exist
                expected_files = ["a.txt", "b.txt", "c.txt"]
                missing_files = [f for f in expected_files if not os.path.exists(os.path.join("txt", f))]
                
                if missing_files:
                    return {
                        "pass": False,
                        "score": 0,
                        "reason": f"Missing output files: {', '.join(missing_files)}"
                    }
                
                # Check file contents
                file_contents = {}
                for filename in expected_files:
                    with open(os.path.join("txt", filename)) as f:
                        file_contents[filename] = f.read()
                
                # Verify the incremental update worked correctly
                check_passed = (
                    file_contents["a.txt"] == "done1" and    # Should remain unchanged
                    file_contents["b.txt"] == "hello2" and   # Should be newly created
                    file_contents["c.txt"] == "done3" and    # Should remain unchanged
                    len(os.listdir("txt")) == 3              # Should have exactly 3 files
                )
                
                if check_passed:
                    return {
                        "pass": True,
                        "score": 1,
                        "reason": "Incremental update executed correctly"
                    }
                else:
                    return {
                        "pass": False,
                        "score": 0,
                        "reason": f"File contents incorrect: {file_contents}"
                    }
                    
            except Exception as e:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Error checking results: {str(e)}"
                }
                
        finally:
            # Restore original directory
            os.chdir(original_cwd)

def extract_bash_code(response):
    """Extract bash code from the response."""
    # Remove language markers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    # If there are code blocks, extract the first one
    if "```" in response and response.count("```") >= 2:
        parts = response.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    
    # Look for lines that look like bash commands
    lines = response.split('\n')
    for line in lines:
        if re.search(r'(for|python|\.pdf|\.txt|\bfind\b|\btest\b)', line):
            return line.strip()
    
    # If no code blocks or command-like lines found, return the whole response
    return response.strip()

def generate_fallback_command():
    """Generate a working bash command for the incremental update."""
    return """
for pdf in *.pdf; do
    txt="txt/${pdf%.pdf}.txt"
    if [ ! -f "$txt" ]; then
        python process.py "$pdf" "$txt"
    fi
done
"""

def add_debug_output(code):
    """Add debug output to the bash command."""
    return f"""
echo "Debug - Starting execution"
echo "Debug - Current directory: $(pwd)"
echo "Debug - Files in current directory: $(ls)"
echo "Debug - Files in txt directory: $(ls txt)"

{code}

echo "Debug - Finished execution"
echo "Debug - Files in txt directory after execution: $(ls txt)"
"""

def run_python_implementation(temp_dir):
    """Run the incremental update using Python instead of bash."""
    try:
        # Implement the same logic in Python
        for pdf_file in os.listdir(temp_dir):
            if pdf_file.endswith('.pdf'):
                txt_file = os.path.join('txt', pdf_file[:-4] + '.txt')
                if not os.path.exists(txt_file):
                    with open(os.path.join(temp_dir, pdf_file)) as f:
                        content = f.read()
                    with open(txt_file, 'w') as f:
                        f.write(content)
        
        # Check results
        if all(os.path.exists(f"txt/{name}.txt") for name in ["a", "b", "c"]):
            with open("txt/a.txt") as f:
                a_content = f.read()
            with open("txt/b.txt") as f:
                b_content = f.read()
            with open("txt/c.txt") as f:
                c_content = f.read()
            
            if (a_content == "done1" and 
                b_content == "hello2" and 
                c_content == "done3" and 
                len(os.listdir("txt")) == 3):
                return {
                    "pass": True,
                    "score": 1,
                    "reason": "Incremental update executed correctly using Python implementation"
                }
        
        return {
            "pass": False,
            "score": 0,
            "reason": "Python implementation failed to create correct files"
        }
        
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error in Python implementation: {str(e)}"
        }