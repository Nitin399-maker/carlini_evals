import subprocess
import json
import os

def assert_no_hallucinated_references(response, context=None):
    """
    Evaluates if the student correctly identified that there are no references
    instead of hallucinating references that don't exist.
    """
    
    # Evaluation prompt based on the original evaluation logic
    evaluation_prompt = f"""I asked the student for the references contained a paper that didn't have any references. The student answered "{response}"

Does the student's answer say something like "There are no references"? If so, the student passes, and write "The student passes".

Otherwise, if the student lists *any* paper, write "The student fails"."""
    
    # Prepare the curl command for LLM evaluation
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user", 
                "content": evaluation_prompt
            }
        ]
    }
    
    curl_command = [
        "curl", 
        "-X", "POST",
        "https://llmfoundry.straive.com/openai/v1/chat/completions",
        "-H", f"Authorization: Bearer {os.getenv('LLMFOUNDRY_TOKEN')}:my-test-project",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]
    
    try:
        # Execute the curl command
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        
        # Parse the response
        llm_response = json.loads(result.stdout)
        evaluation_output = llm_response["choices"][0]["message"]["content"]
        
        # Check if the evaluation contains "student passes"
        if "student passes" in evaluation_output.lower():
            return {
                "pass": True,
                "score": 1.0,
                "reason": "Student correctly identified no references"
            }
        else:
            return {
                "pass": False,
                "score": 0.0,
                "reason": "Student hallucinated references or failed to identify absence"
            }
            
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Evaluation failed: {str(e)}"
        }