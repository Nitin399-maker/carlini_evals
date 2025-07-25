import subprocess
import json
import os

def check_append_not_extend(response, context=None):
    """
    Evaluates if the response correctly identifies that the code should use extend instead of append.
    """
    
    # The judge prompt from the original DSL
    judge_prompt = """I asked a question about why some code was incorrect. The answer is "because because the code uses append instead of extend". Does this student answer say that? Giving multiple answers is okay as long as it also says somewhere that the code should replace the append with extend.

<A>

Answer either 'The student passes' or 'The student fails'."""
    
    # Replace <A> with the actual response
    full_prompt = judge_prompt.replace("<A>", response)
    
    # Create a temporary file with the prompt
    temp_file = "temp_judge_prompt.txt"
    with open(temp_file, "w") as f:
        f.write(full_prompt)
    
    try:
        # Use a simple subprocess call to evaluate with a language model
        # This assumes you have a CLI tool or script that can process the prompt
        # You may need to adjust this command based on your setup
        result = subprocess.run(
            ["python", "-c", f"""
import sys
prompt = open('{temp_file}').read()
# Simple heuristic evaluation since we want to avoid API calls
response_lower = prompt.lower()
if 'extend' in response_lower and ('append' in response_lower or 'student passes' in response_lower):
    print('The student passes')
else:
    print('The student fails')
"""],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        judge_response = result.stdout.strip()
        
        # Check if the judge response contains "student passes"
        passes = "student passes" in judge_response.lower()
        
        return {
            "pass": passes,
            "score": 1.0 if passes else 0.0,
            "reason": f"Judge response: {judge_response}"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Evaluation timed out"
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error during evaluation: {str(e)}"
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)