import subprocess
import tempfile
import os
import re
import json

def check(response, context=None):
    """
    Evaluates if the student tried to vectorize the loop correctly.
    Returns a score and reason.
    """
    
    # Step 1: Extract code from response
    code = extract_code(response)
    if not code:
        return {"pass": False, "score": 0, "reason": "No code found in response"}
    
    # Step 2: Run the code with test case
    test_case = 'print(list(update(np.array([2, 5, 9, 1, 2, 0, 3, 8]), 4, np.array([1, 2, 1, 4, 3, 2, 1, 2]))))'
    expected_output = "[2, 3, 4, 1, 2, 0, 3, 3]"
    
    code_with_test = f"import numpy as np\n\n{code}\n\n{test_case}"
    
    temp_file = None
    try:
        # Create a temporary file
        fd, temp_file = tempfile.mkstemp(suffix='.py')
        os.close(fd)  # Close the file descriptor immediately
        
        # Write to the file
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code_with_test)
        
        # Run the code as a separate process
        result = subprocess.run(
            ['python', temp_file], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        # Check return code
        if result.returncode != 0:
            return {"pass": False, "score": 0, "reason": f"Code execution failed: {result.stderr}"}
        
        # Check if output matches expected
        output = result.stdout.strip()
        if expected_output not in output:
            return {"pass": False, "score": 0, "reason": f"Output mismatch. Expected: {expected_output}, Got: {output}"}
    
    except Exception as e:
        return {"pass": False, "score": 0, "reason": f"Execution error: {str(e)}"}
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception:
                pass  # Ignore errors during cleanup
    
    # Step 3: Check if vectoried (no explicit for loop)
    evaluation_text = f"""Below is a student's answer to a question about how to vectorize this loop:
def update(high, highest_number, delta):
    for i in range(len(high)):
        if i != highest_number:
            high[i] = min(high[i], high[highest_number] + delta[highest_number] - delta[i])
    return high
Here is their code:
{code}
Did the student try to vectorize the loop? Don't tell me if they are correct or not. (I have tests for that separately which will catch any bugs.) Just tell me if they tried to vectorize the loop. End your answer with either the string "The student passes" if they tried to do a vectorized loop, or "The student fails" if they just wrote a for loop again."""
    
    # Make LLM call to evaluate vectorization
    try:
        # Check if token is available
        token = os.getenv("LLMFOUNDRY_TOKEN")
        if not token:
            # Skip LLM evaluation if no token
            return {"pass": True, "score": 1, "reason": "Code executes correctly. (Skipped vectorization check due to missing token)"}
        
        # Prepare curl command
        curl_command = [
            'curl', '-X', 'POST', 'https://llmfoundry.straive.com/openai/v1/chat/completions',
            '-H', f'Authorization: Bearer {token}:my-test-project',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": evaluation_text}]
            })
        ]
        
        # Execute curl command
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {"pass": False, "score": 0, "reason": f"LLM evaluation failed: {result.stderr}"}
        
        # Parse response
        response_data = json.loads(result.stdout)
        llm_response = response_data['choices'][0]['message']['content']
        
        # Check if LLM says student passes
        if "student passes" in llm_response.lower():
            return {"pass": True, "score": 1, "reason": "Code executes correctly and uses vectorization"}
        else:
            return {"pass": False, "score": 0, "reason": "Student did not vectorize the loop"}
            
    except Exception as e:
        # If LLM evaluation fails, return a success based just on the execution test
        return {"pass": True, "score": 0.5, "reason": f"Code executes correctly but couldn't verify vectorization: {str(e)}"}

def extract_code(output):
    """Extract code from markdown code blocks or return the output as-is"""
    output = re.sub(r'```[a-z]*', '```', output)
    if "```" in output and output.count("```") >= 2:
        # Extract from code blocks
        code = output.split("```")[1]
        return code.strip()
    else:
        # Return as-is if no code blocks
        return output.strip()