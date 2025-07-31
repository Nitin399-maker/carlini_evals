import subprocess
import tempfile
import os
import re
import platform
import sys

def check_assertion(response, context=None):
    """
    Test if a model can implement a bash 1-liner to find files that don't contain 'asdf' (case-ignore).
    Expected files in output: hello, this, asdf (but NOT there, lower)
    """
    
    def extract_code(output):
        """Extract code from LLM response, handling markdown code blocks"""
        output = re.sub(r'```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1].strip()
        return output.strip()
    
    def setup_test_files(temp_dir):
        """Create test files in temporary directory"""
        files = {
            "hello": "this is a test",
            "there": "test this ASDF", 
            "this": "whatever thing",
            "asdf": "zzzthing",
            "lower": "test this asdf"
        }
        
        for filename, content in files.items():
            with open(os.path.join(temp_dir, filename), "w") as f:
                f.write(content)

    def run_grep_command(temp_dir, bash_code):
        """Run the grep command, handling different OS environments"""
        is_windows = platform.system() == 'Windows'
        
        if is_windows:
            # Convert bash grep command to PowerShell equivalent
            if 'grep' in bash_code.lower():
                # Create a simple Python script to simulate grep behavior
                script_path = os.path.join(temp_dir, "grep_script.py")
                with open(script_path, "w", encoding='utf-8') as f:
                    f.write("""
import os
import re
import sys

def check_file(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read().lower()
            return 'asdf' not in content
    except:
        return False

# Get all files in current directory
files = [f for f in os.listdir('.') if os.path.isfile(f)]

# Filter files that don't contain 'asdf'
matching_files = [f for f in files if check_file(f)]

# Print results
print('\\n'.join(sorted(matching_files)))
""")
                
                # Run the Python script
                result = subprocess.run(
                    [sys.executable, script_path],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # Try to run the command as-is if it doesn't use grep
                result = subprocess.run(
                    bash_code,
                    shell=True,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
        else:
            # On Unix-like systems, run the bash command directly
            result = subprocess.run(
                bash_code,
                shell=True,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
        
        return result
    
    # Extract bash code from response
    bash_code = extract_code(response)
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup test files
        setup_test_files(temp_dir)
        
        try:
            # Run the command with appropriate handling for the OS
            result = run_grep_command(temp_dir, bash_code)
            
            output = result.stdout.strip()
            
            # Check if command succeeded
            if result.returncode != 0:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Command failed with error: {result.stderr}"
                }
            
            # Expected files: hello, this, asdf (files that don't contain 'asdf' case-insensitive)
            # Should NOT include: there (contains 'ASDF'), lower (contains 'asdf')
            expected_present = ["hello", "this", "asdf"]
            expected_absent = ["there", "lower"]
            
            # Normalize output: split into lines and sort
            output_files = sorted(output.split())
            
            all_checks_pass = True
            reasons = []
            
            # Check that expected files are present
            for filename in expected_present:
                if any(file.strip() == filename for file in output_files):
                    reasons.append(f"✓ '{filename}' correctly included")
                else:
                    all_checks_pass = False
                    reasons.append(f"✗ '{filename}' missing from output")
            
            # Check that files with 'asdf' content are absent
            for filename in expected_absent:
                if not any(file.strip() == filename for file in output_files):
                    reasons.append(f"✓ '{filename}' correctly excluded")
                else:
                    all_checks_pass = False
                    reasons.append(f"✗ '{filename}' should not be in output")
            
            return {
                "pass": all_checks_pass,
                "score": 1.0 if all_checks_pass else 0.0,
                "reason": "; ".join(reasons) + f"\nActual output: {output}"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "pass": False,
                "score": 0,
                "reason": "Command timed out"
            }
        except Exception as e:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Error running command: {str(e)}"
            }