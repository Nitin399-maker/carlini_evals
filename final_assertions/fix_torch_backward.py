import subprocess
import tempfile
import os
import re

def get_assertions(response, context=None):
    """
    Evaluates PyTorch code fix by extracting code, running it, and checking output.
    """
    
    def extract_code(text):
        """Extract code from markdown code blocks or plain text"""
        # Clean up special characters
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove language specifiers from code blocks
        text = re.sub('```[a-z]*', '```', text)
        
        if "```" in text and text.count("```") >= 2:
            # Extract from code blocks
            code = text.split("```")[1]
        else:
            # Use the entire response as code
            code = text
        
        return code.strip()
    
    def run_python_code(code):
        """Execute Python code and return output"""
        try:
            # Add UTF-8 encoding declaration
            code_with_encoding = "# -*- coding: utf-8 -*-\n" + code
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', encoding='utf-8', delete=False) as f:
                f.write(code_with_encoding)
                temp_file = f.name
            
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            os.unlink(temp_file)
            
            if result.returncode != 0:
                return f"ERROR: {result.stderr}"
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            return "ERROR: Code execution timed out"
        except Exception as e:
            return f"ERROR: {str(e)}"
        finally:
            if 'temp_file' in locals() and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def check_substring(text, substring):
        """Check if substring exists in text"""
        return substring in text
    
    try:
        # Extract code from the response
        extracted_code = extract_code(response)
        
        # Run the extracted code
        output = run_python_code(extracted_code)
        
        # Check for both required substrings
        has_tensor = check_substring(output, "tensor")
        has_grad_fn = check_substring(output, "grad_fn=<Add")
        
        # Both conditions must be true
        passes = has_tensor and has_grad_fn
        
        return {
            "pass": passes,
            "score": 1.0 if passes else 0.0,
            "reason": f"Code execution output: {output[:200]}..." if len(output) > 200 else f"Code execution output: {output}",
            "assertion": {
                "type": "python-code-fix",
                "has_tensor": has_tensor,
                "has_grad_fn": has_grad_fn,
                "extracted_code": extracted_code[:500] + "..." if len(extracted_code) > 500 else extracted_code
            }
        }
        
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error during assertion: {str(e)}",
            "assertion": {
                "type": "python-code-fix",
                "error": str(e)
            }
        }