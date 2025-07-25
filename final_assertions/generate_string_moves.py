import re
import subprocess
import tempfile
import os

def check(response, context=None):
    """
    Promptfoo assertion function that extracts code from LLM response,
    runs it with a test case, and checks if the output contains the expected answer.
    """
    
    # Step 1: Extract code from response (equivalent to ExtractCode)
    def extract_code(output):
        # Clean up potential smart quotes and other special characters
        output = output.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of backticks
            parts = output.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        # If no code blocks found, return the entire output
        return output.strip()
    
    try:
        code = extract_code(response)
        
        # Step 2: Prepare test case (equivalent to PythonRun)
        test_case = "print(set(move('abcdef')))"
        full_code = f"# -*- coding: utf-8 -*-\n{code}\n\n{test_case}"
        
        # Step 3: Run the Python code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', encoding='utf-8', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Code execution failed: {result.stderr}'
                }
            
            output = result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            return {
                'pass': False,
                'score': 0,
                'reason': 'Code execution timed out'
            }
            
    except Exception as e:
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.unlink(temp_file)
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error running code: {str(e)}'
        }
    
    # Step 4: Check if output contains expected answer (equivalent to SubstringEvaluator)
    expected_answer = "{'abcdef', 'abcdfe', 'abcedf', 'abcefd', 'abcfde', 'abdcef', 'abdecf', 'abdefc', 'abecdf', 'abefcd', 'abfcde', 'acbdef', 'acdbef', 'acdebf', 'acdefb', 'adbcef', 'adebcf', 'adefbc', 'aebcdf', 'aefbcd', 'afbcde', 'bacdef', 'bcadef', 'bcdaef', 'bcdeaf', 'bcdefa', 'cabdef', 'cdabef', 'cdeabf', 'cdefab', 'dabcef', 'deabcf', 'defabc', 'eabcdf', 'efabcd', 'fabcde'}"
    
    # Normalize both expected and actual output for comparison
    def normalize_set_string(s):
        # Convert string representation of set to normalized form
        items = set(s.strip("{}").replace("'", "").split(", "))
        return "{" + ", ".join(sorted(items)) + "}"
    
    try:
        normalized_output = normalize_set_string(output)
        normalized_expected = normalize_set_string(expected_answer)
        
        if normalized_output == normalized_expected:
            return {
                'pass': True,
                'score': 1,
                'reason': 'Code executed successfully and produced expected output'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Expected output not found. Got: {output}'
            }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error comparing outputs: {str(e)}'
        }