import json
import re
import subprocess
import tempfile
import os
import time

def run_test(response, context=None):
    """Run the test with proper file handling."""
    
    # Create temp directory instead of using /tmp
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Setup the test file in temp directory
            txt = "it was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of Light, it was the season of Darkness, it was the spring of hope, it was the winter of despair, we had everything before us, we had nothing before us, we were all going direct to Heaven, we were all going direct the other way"
            
            input_file = os.path.join(temp_dir, "file.txt")
            with open(input_file, "w", encoding='utf-8') as f:
                f.write(txt)
            
            # Extract code from response
            code = extract_code(response)
            if not code:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": "No code found in response"
                }
            
            # Replace /tmp/file.txt with the correct path
            code = code.replace('/tmp/file.txt', input_file.replace('\\', '\\\\'))
            
            # Check if code attempts parallelization
            parallelization_check = check_parallelization(code)
            
            # Run the code and get results
            try:
                result = run_python_code(code, temp_dir)
                merged_dict = merge_json_outputs(result)
                expected = {'the': 11, 'it': 10, 'was': 10, 'of': 10, 'we': 4, 'times,': 2, 'age': 2, 'epoch': 2, 'season': 2, 'had': 2, 'before': 2, 'us,': 2, 'were': 2, 'all': 2, 'going': 2, 'direct': 2, 'best': 1, 'worst': 1, 'wisdom,': 1, 'foolishness,': 1, 'belief,': 1, 'incredulity,': 1, 'Light,': 1, 'Darkness,': 1, 'spring': 1, 'hope,': 1, 'winter': 1, 'despair,': 1, 'everything': 1, 'nothing': 1, 'to': 1, 'Heaven,': 1, 'other': 1, 'way': 1}
                
                word_count_correct = merged_dict == expected
                
                # Both conditions must pass
                overall_pass = word_count_correct and parallelization_check
                return {
                    "pass": overall_pass,
                    "score": 1.0 if overall_pass else 0.0,
                    "reason": f"Word count correct: {word_count_correct}, Parallelization attempted: {parallelization_check}. Expected: {expected}, Got: {merged_dict}"
                }
            except Exception as e:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Error running code: {str(e)}"
                }
                
        except Exception as e:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Setup error: {str(e)}"
            }

def extract_code(response):
    """Extract Python code from the response, keeping main function"""
    response = re.sub('```[a-z]*', '```', response)
    if "```" in response and response.count("```") >= 2:
        # Extract code between first pair of ```
        code = response.split("```")[1]
        return code.strip()
    else:
        # If no code blocks, assume the entire response is code
        return response.strip()

def check_parallelization(code):
    """Check if the code attempts parallelization"""
    parallel_keywords = [
        'multiprocessing', 'threading', 'concurrent.futures',
        'Pool', 'Process', 'Thread', 'ThreadPoolExecutor',
        'ProcessPoolExecutor', 'parallel', 'cores'
    ]
    code_lower = code.lower()
    for keyword in parallel_keywords:
        if keyword.lower() in code_lower:
            return True
    return False

def run_python_code(code, temp_dir):
    """Run the Python code and capture stdout"""
    script_path = os.path.join(temp_dir, "script.py")
    try:
        # Write the code to a file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Wait a moment to ensure file is written
        time.sleep(0.1)
        
        # Run the code
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Code execution failed: {result.stderr}")
        
        return result.stdout
        
    except Exception as e:
        raise Exception(f"Error running code: {str(e)}")
    finally:
        # Try to clean up the script file
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
        except:
            pass

def merge_json_outputs(output_text):
    """Merge multiple JSON dictionaries from the output"""
    merged = {}
    for line in output_text.split("\n"):
        line = line.strip()
        if line and '{' in line:
            try:
                d = json.loads(line)
                for k, v in d.items():
                    merged[k] = merged.get(k, 0) + v
            except json.JSONDecodeError:
                continue
    return merged