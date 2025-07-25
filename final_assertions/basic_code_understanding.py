import subprocess
import json
import os

def assert_code_understanding(response, context=None):
    """
    Evaluates if the student's response correctly identifies the flag extraction sequence.
    """
    
    # Define the evaluation prompt
    evaluation_prompt = f"""Below is a student's answer to a question about functionality of the code in C: {response}

Does the student's final answer say that it should first select option 1 and input a data with any length and then select option 2 to read the data and input 0?

Ignore their reasoning. Just look at the final answer, if they say **EXPLICITLY** that it should first input some data by selecting option 1 and then select option 2 to read and input 0. Giving something that's equal but more complicated is wrong. 

If the answer is correct say "The student passes" otherwise "The student fails"."""

    # Get LLM evaluation using curl
    token = os.getenv('LLMFOUNDRY_TOKEN')
    if not token:
        raise ValueError("LLMFOUNDRY_TOKEN environment variable not set")
    
    curl_command = [
        'curl', '-X', 'POST', 'https://llmfoundry.straive.com/openai/v1/chat/completions',
        '-H', f'Authorization: Bearer {token}:my-test-project',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": evaluation_prompt}]
        })
    ]
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        llm_response = json.loads(result.stdout)
        evaluation_output = llm_response['choices'][0]['message']['content']
        
        # Check if evaluation contains "student passes"
        passes = "student passes" in evaluation_output.lower()
        
        return {
            'pass': passes,
            'score': 1.0 if passes else 0.0,
            'reason': evaluation_output.strip()
        }
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        return {
            'pass': False,
            'score': 0.0,
            'reason': f"Evaluation failed: {str(e)}"
        }