import tempfile
import os
import re
import sys
from io import StringIO
from contextlib import redirect_stdout

def assert_python_traceback_fix(response, context=None):
    """
    Evaluates if the LLM response correctly fixes the Python traceback program.
    Expected to find "x: 5" and "y: 6" in the output.
    """
    
    def extract_code(output, keep_main=True):
        """Extract code from response, handling code blocks"""
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of ```
            parts = output.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # If no code blocks found, assume entire response is code
        return output.strip()
    
    def run_python_code(code):
        """Run Python code using exec() and return output"""
        try:
            # Redirect stdout to capture print statements
            output = StringIO()
            with redirect_stdout(output):
                # Use exec() to run the code
                exec(code, globals())
            return output.getvalue()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def check_substring(output, substr):
        """Check if substring exists in output"""
        return substr in output
    
    # Extract code from the LLM response
    extracted_code = extract_code(response, keep_main=True)
    
    # Run the extracted code
    execution_output = run_python_code(extracted_code)
    
    # Check for both required substrings
    has_x_5 = check_substring(execution_output, "x: 5")
    has_y_6 = check_substring(execution_output, "y: 6")
    
    # Both conditions must be true
    success = has_x_5 and has_y_6
    
    return {
        'pass': success,
        'score': 1.0 if success else 0.0,
        'reason': f"Execution output: {execution_output[:200]}... | Found 'x: 5': {has_x_5}, Found 'y: 6': {has_y_6}"
    }