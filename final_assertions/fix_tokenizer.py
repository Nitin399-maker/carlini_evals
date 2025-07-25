import subprocess
import tempfile
import re
import os

def assert_tokenizer_fix(response, context=None):
    """
    Evaluates if the LLM response correctly fixes the tokenizer regex issue.
    """
    
    def extract_code(output):
        """Extract code from response, handling code blocks."""
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract content between first pair of ```
            parts = output.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        # If no code blocks, return the whole output
        return output.strip()
    
    def run_python_code(code, test_case):
        """Run Python code with test case using subprocess."""
        full_code = code + "\n\n" + test_case
        
        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        try:
            # Run the code
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {str(e)}"
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def check_substring(output, expected_substr):
        """Check if expected substring is in output."""
        return expected_substr in output
    
    # Extract code from LLM response
    extracted_code = extract_code(response)
    
    # Prepare test case
    test_case = "print(Tokenizer('sin(3+2*4)-cos(15)').tokens)"
    expected_answer = "['sin', '(', '3', '+', '2', '*', '4', ')', '-', 'cos', '(', '15', ')']"
    
    # Add import if not present
    if "import re" not in extracted_code:
        extracted_code = "import re\n" + extracted_code
    
    # Run the code with test case
    output = run_python_code(extracted_code, test_case)
    
    # Check if expected output is present
    success = check_substring(output, expected_answer)
    
    return {
        "pass": success,
        "score": 1.0 if success else 0.0,
        "reason": f"Expected '{expected_answer}' in output. Got: '{output.strip()}'"
    }