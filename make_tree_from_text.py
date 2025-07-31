import subprocess
import tempfile
import os
import re

def assert_tree_creation(response, context=None):
    """
    Assertion function for Promptfoo to test if the model can create a tree from a string.
    
    Args:
        response: The LLM response containing code
        context: Additional context (unused)
    
    Returns:
        dict: Result with pass/fail status and details
    """
    
    def extract_code(output):
        """Extract code from the LLM response, keeping main function."""
        # Remove language specifiers from code blocks
        output = re.sub('```[a-z]*', '```', output)
        
        if "```" in output and output.count("```") >= 2:
            # Extract code from between triple backticks
            code = output.split("```")[1]
        else:
            # No code blocks found, use entire response
            code = output
        
        return code.strip()
    
    def run_python_code(code):
        """Run the extracted Python code and return output."""
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run the Python code
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode != 0:
                return None, f"Code execution failed: {result.stderr}"
            
            return result.stdout.strip(), None
            
        except subprocess.TimeoutExpired:
            if 'temp_file' in locals():
                os.unlink(temp_file)
            return None, "Code execution timed out"
        except Exception as e:
            if 'temp_file' in locals():
                os.unlink(temp_file)
            return None, f"Error running code: {str(e)}"
    
    def check_substring(output, target_substring):
        """Check if target substring exists in output."""
        return target_substring in output
    
    # Extract code from response
    try:
        extracted_code = extract_code(response)
        if not extracted_code:
            return {
                "pass": False,
                "score": 0,
                "reason": "No code found in response"
            }
        
        # Run the extracted code
        output, error = run_python_code(extracted_code)
        
        if error:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Code execution error: {error}"
            }
        
        # Check if the expected tree structure is in the output
        expected_tree = "(1 (2 (3 4 5 6) (7 8)) (9 10 (11 12)))"
        
        if check_substring(output, expected_tree):
            return {
                "pass": True,
                "score": 1,
                "reason": f"Successfully generated expected tree structure: {expected_tree}"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Expected '{expected_tree}' in output, but got: {output}"
            }
            
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Assertion error: {str(e)}"
        }