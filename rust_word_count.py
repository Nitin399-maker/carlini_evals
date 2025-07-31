import subprocess
import tempfile
import os
import json
import re
import platform
import sys

def assert_rust_word_count(response, context=None):
    """
    Evaluates if the LLM response contains a working Rust word counting program.
    """
    
    # Check if Rust is installed
    try:
        # Check Rust compiler availability
        subprocess.run(
            ["rustc", "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return {
            "pass": False,
            "score": 0,
            "reason": "Rust compiler (rustc) not found. Please install Rust to run this assertion."
        }
    
    # Setup - create the test file in a platform-appropriate temp directory
    test_text = "it was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of Light, it was the season of Darkness, it was the spring of hope, it was the winter of despair, we had everything before us, we had nothing before us, we were all going direct to Heaven, we were all going direct the other way"
    
    temp_dir = tempfile.mkdtemp()
    test_file_path = os.path.join(temp_dir, "file.txt")
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_text)
    
    # Expected answer
    expected = {'the': 11, 'it': 10, 'was': 10, 'of': 10, 'we': 4, 'times,': 2, 'age': 2, 'epoch': 2, 'season': 2, 'had': 2, 'before': 2, 'us,': 2, 'were': 2, 'all': 2, 'going': 2, 'direct': 2, 'best': 1, 'worst': 1, 'wisdom,': 1, 'foolishness,': 1, 'belief,': 1, 'incredulity,': 1, 'Light,': 1, 'Darkness,': 1, 'spring': 1, 'hope,': 1, 'winter': 1, 'despair,': 1, 'everything': 1, 'nothing': 1, 'to': 1, 'Heaven,': 1, 'other': 1, 'way': 1}
    
    # Extract code from response
    code = extract_rust_code(response)
    if not code:
        return {
            "pass": False,
            "score": 0,
            "reason": "No Rust code found in response"
        }
    
    # Modify code to use the correct test file path
    code = code.replace("/tmp/file.txt", test_file_path.replace("\\", "\\\\"))
    
    # Run the Rust code
    try:
        output = run_rust_code(code, temp_dir)
        if not output:
            return {
                "pass": False,
                "score": 0,
                "reason": "Rust program produced no output"
            }
        
        # Extract and parse JSON from output
        json_data = extract_json_from_output(output)
        if json_data is None:
            return {
                "pass": False,
                "score": 0,
                "reason": "Could not extract valid JSON from program output"
            }
        
        # Check if the output matches expected results
        if check_json_subset(expected, json_data):
            return {
                "pass": True,
                "score": 1,
                "reason": "Rust program correctly counts words and outputs valid JSON"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Word count mismatch. Expected subset: {expected}, Got: {json_data}"
            }
            
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error running Rust code: {str(e)}"
        }
    finally:
        # Clean up
        try:
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass

def extract_rust_code(response):
    """Extract Rust code from the LLM response."""
    response = re.sub(r'```[a-z]*', '```', response)
    
    if "```" in response:
        # Extract code between triple backticks
        parts = response.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    
    # If no code blocks found, assume the entire response is code
    return response.strip()

def run_rust_code(code, temp_dir):
    """Compile and run the Rust code, returning stdout."""
    rust_file = os.path.join(temp_dir, "main.rs")
    
    # Determine binary file name based on platform
    binary_name = "main.exe" if platform.system() == "Windows" else "main"
    binary_file = os.path.join(temp_dir, binary_name)
    
    # Write Rust code to file
    with open(rust_file, "w", encoding="utf-8") as f:
        f.write(code)
    
    # Find rustc executable
    rustc_cmd = "rustc"
    
    # Compile Rust code
    compile_result = subprocess.run(
        [rustc_cmd, "-o", binary_file, rust_file],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if compile_result.returncode != 0:
        raise Exception(f"Compilation failed: {compile_result.stderr}")
    
    # Run the compiled binary
    run_result = subprocess.run(
        [binary_file],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if run_result.returncode != 0:
        raise Exception(f"Runtime error: {run_result.stderr}")
    
    return run_result.stdout

def extract_json_from_output(output):
    """Extract JSON from program output."""
    output = output.replace("```json", "```")
    
    # Try extracting from code blocks first
    if "```" in output:
        parts = output.split("```")
        for part in parts[1::2]:  # Every other part starting from index 1
            try:
                return json.loads(part.strip())
            except json.JSONDecodeError:
                continue
    
    # Try parsing the entire output as JSON
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON-like patterns in the output
    json_pattern = r'\{[^}]+\}'
    matches = re.findall(json_pattern, output)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    return None

def check_json_subset(expected, actual):
    """Check if all expected key-value pairs are present in actual."""
    if not isinstance(actual, dict):
        return False
    
    for key, value in expected.items():
        if key not in actual:
            return False
        if actual[key] != value:
            return False
    
    return True