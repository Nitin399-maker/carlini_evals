import subprocess
import tempfile
import os
import re

def test_vague_loop_format(response, context=None):
    """
    Test if the model can follow vague instructions for how to print IDs following an example.
    Evaluates: ExtractCode(keep_main=True) >> PythonRun() >> SubstringEvaluator checks
    """
    
    def extract_code_with_main(text):
        """Extract code and ensure it's runnable with main"""
        # Remove language specifiers from code blocks
        text = re.sub(r'```[a-z]*', '```', text)
        
        if "```" in text:
            # Extract code from markdown blocks
            code = text.split("```")[1]
        else:
            # Use the entire response as code
            code = text
            
        # If the code doesn't have a main block, it should still be runnable
        return code.strip()
    
    def run_python_code(code):
        """Run Python code and capture output"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['python', temp_file], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.returncode != 0:
                return None, f"Python execution failed: {result.stderr}"
            
            return result.stdout, None
            
        except subprocess.TimeoutExpired:
            return None, "Code execution timed out"
        except Exception as e:
            return None, f"Error running code: {str(e)}"
    
    def check_required_outputs(output):
        """Check if output contains all required ID patterns"""
        if not output:
            return False, "No output generated"
        
        # Check for the example pattern first
        if "2401_001" not in output:
            return False, "Missing required example pattern 2401_001"
        
        missing_patterns = []
        
        # Check all required patterns: months 1-12, ids 1-3
        for month in range(1, 13):
            for id_num in range(1, 4):
                pattern = f"24{month:02}_{id_num:03}"
                if pattern not in output:
                    missing_patterns.append(pattern)
        
        if missing_patterns:
            return False, f"Missing required patterns: {missing_patterns[:5]}{'...' if len(missing_patterns) > 5 else ''}"
        
        return True, "All required patterns found"
    
    # Extract code from response
    try:
        code = extract_code_with_main(response)
        if not code:
            return {
                'pass': False,
                'score': 0.0,
                'reason': 'No code found in response'
            }
    except Exception as e:
        return {
            'pass': False,
            'score': 0.0,
            'reason': f'Error extracting code: {str(e)}'
        }
    
    # Run the extracted code
    output, error = run_python_code(code)
    if error:
        return {
            'pass': False,
            'score': 0.0,
            'reason': error
        }
    
    # Check if output contains all required patterns
    success, message = check_required_outputs(output)
    
    if success:
        return {
            'pass': True,
            'score': 1.0,
            'reason': 'Code successfully generated all required ID patterns'
        }
    else:
        return {
            'pass': False,
            'score': 0.0,
            'reason': message
        }