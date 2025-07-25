import subprocess
import json
import os

def get_assertion(response, context=None):
    evaluation_prompt = """Below is a student's answer to a question on what is missing from some pancake recipe: <A>

Does the student mention that baking powder or baking soda is missing? Think out loud, and then end your answer with either the string "The student passes" or "The student fails"."""
    
    # Replace <A> with the actual response
    evaluation_text = evaluation_prompt.replace("<A>", response)
    
    # Prepare the curl command
    curl_command = [
        "curl", "-X", "POST", 
        "https://llmfoundry.straive.com/openai/v1/chat/completions",
        "-H", f"Authorization: Bearer {os.getenv('LLMFOUNDRY_TOKEN')}:my-test-project",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": evaluation_text}]
        })
    ]
    
    # Execute the curl command
    result = subprocess.run(curl_command, capture_output=True, text=True)
    
    if result.returncode != 0:
        return {
            "pass": False,
            "score": 0,
            "reason": f"API call failed: {result.stderr}"
        }
    
    try:
        response_data = json.loads(result.stdout)
        eval_response = response_data["choices"][0]["message"]["content"]
        
        # Check if the evaluation response contains "student passes"
        passes = "student passes" in eval_response.lower()
        
        return {
            "pass": passes,
            "score": 1 if passes else 0,
            "reason": f"Evaluation result: {eval_response}"
        }
        
    except (json.JSONDecodeError, KeyError) as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Failed to parse API response: {e}"
        }
        
        