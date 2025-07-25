import re
import subprocess
import tempfile
import os
  
def assert_bnf_evaluator(response, context=None):
    """
    Promptfoo assertion that extracts Python code from LLM response,
    runs it with test case, and checks for expected output.
    """
    # Extract code from response (similar to ExtractCode)
    def extract_code(text):
        # Remove non-ASCII characters to prevent encoding issues
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        # Remove language specifiers from code blocks
        text = re.sub(r'```[a-z]*', '```', text)
        if "```" in text and text.count("```") >= 2:
            # Extract code between first pair of triple backticks
            parts = text.split("```")
            if len(parts) >= 2:
                return parts[1].strip()
        # If no code blocks found, assume entire response is code
        return text.strip()
    
    # Test case and expected answer
    test_case = "print(round(evaluate('sin(35+2*4)-cos(15)'), 5))"
    expected_answer = "-0.07209"
    
    try:
        # Extract Python code from response
        code = extract_code(response)
        
        # Combine code with test case
        full_code = code + "\n\n" + test_case
        
        # Write code to temporary file and execute with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8', errors='ignore') as f:
            # Add encoding declaration
            f.write("# -*- coding: utf-8 -*-\n")
            f.write(full_code)
            temp_file = f.name
        
        try:
            # Run Python code
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0.0,
                    'reason': f'Code execution failed: {result.stderr}'
                }
            
            output = result.stdout.strip()
            
            # Check if expected answer is in output
            if expected_answer in output:
                return {
                    'pass': True,
                    'score': 1.0,
                    'reason': f'Code executed successfully and produced expected output: {expected_answer}'
                }
            else:
                return {
                    'pass': False,
                    'score': 0.0,
                    'reason': f'Expected "{expected_answer}" but got: {output}'
                }
        except subprocess.TimeoutExpired:
            return {
                'pass': False,
                'score': 0.0,
                'reason': 'Code execution timed out'
            }
        except Exception as e:
            import traceback
            return {
                'pass': False,
                'score': 0.0,
                'reason': f'Error executing code: {str(e)}\nTraceback: {traceback.format_exc()}'
            }
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    except Exception as e:
        import traceback
        return {
            'pass': False,
            'score': 0.0,
            'reason': f'Error processing response: {str(e)}\nTraceback: {traceback.format_exc()}'
        }