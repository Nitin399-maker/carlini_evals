import subprocess
import json
import os

def get_assertion(response, context=None):
    # The evaluation prompt that checks if the student mentions innerHTML clearing event listeners
    evaluation_prompt = """Below is a student's answer to a question about what a particular instruction does: """ + response + """

Does the student's say something similar to "editing the innerHTML clears event listeners"?

If the answer is correct say "The student passes" otherwise "The student fails"."""
    token = os.getenv("LLMFOUNDRY_TOKEN")
    # Make LLM call to evaluate the response
    try:
        curl_command = [
            "curl", "-X", "POST", 
            "https://llmfoundry.straive.com/openai/v1/chat/completions",
            "-H", f"Authorization: Bearer {token}:my-test-project",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": evaluation_prompt}]
            })
        ]
        
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {"pass": False, "score": 0, "reason": f"LLM call failed: {result.stderr}"}
        
        llm_response = json.loads(result.stdout)
        evaluation_result = llm_response["choices"][0]["message"]["content"].strip()
        
        # Check if the evaluation contains "student passes" (case insensitive)
        passes = "student passes" in evaluation_result.lower()
        
        return {
            "pass": passes,
            "score": 1 if passes else 0,
            "reason": f"Evaluation result: {evaluation_result}"
        }
        
    except subprocess.TimeoutExpired:
        return {"pass": False, "score": 0, "reason": "LLM call timed out"}
    except json.JSONDecodeError as e:
        return {"pass": False, "score": 0, "reason": f"Failed to parse LLM response: {e}"}
    except Exception as e:
        return {"pass": False, "score": 0, "reason": f"Error during evaluation: {e}"}