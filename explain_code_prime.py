import subprocess
import json
import os

def get_assertion(response, context=None):
    """
    Evaluates if the LLM response correctly identifies that the code calculates the first 20 primes.
    """
    
    # Prepare the evaluation prompt
    eval_prompt = (
        "I showed a student some code that calculates 20 primes. I then tested their understanding by asking them to explain it to me. "
        "I'm going to show you their answer, I want you to evaluate whether or not their answer says something to the effect of "
        "\"it calculates the first 20 primes\". Do not judge their reasoning, just tell me if they got it right.\n"
        f"Student Answer: \"{response}\"\n\n"
        "Think out loud then answer either \"The student passes\" or \"The student fails\"."
    )
    
    # Get the API token from environment
    token = os.getenv("LLMFOUNDRY_TOKEN")
    if not token:
        return {
            'pass': False,
            'score': 0,
            'reason': 'LLMFOUNDRY_TOKEN environment variable not set'
        }
    
    # Prepare the curl command
    curl_data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": eval_prompt}]
    }
    
    try:
        # Make the API call using subprocess
        result = subprocess.run([
            'curl', '-X', 'POST', 
            'https://llmfoundry.straive.com/openai/v1/chat/completions',
            '-H', f'Authorization: Bearer {token}:my-test-project',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(curl_data)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Curl command failed: {result.stderr}'
            }
        
        # Parse the response
        api_response = json.loads(result.stdout)
        eval_output = api_response['choices'][0]['message']['content']
        
        # Check if the evaluation indicates the student passes
        passes = "student passes" in eval_output.lower()
        
        return {
            'pass': passes,
            'score': 1 if passes else 0,
            'reason': f'Evaluator response: {eval_output}'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'API call timed out'
        }
    except json.JSONDecodeError as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Failed to parse API response: {e}'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Unexpected error: {e}'
        }