import subprocess
import json
import os

def check_bug_explanation(response, context=None):
    """
    Evaluates if the student correctly identifies the bug in parallel wordcount code.
    The correct answer is that chunks could contain overlapping data.
    """
    
    # Prepare the evaluation prompt
    eval_prompt = f"""Below is a student's explanation for why some parallel wordcounting code is not working correctly. You don't need to see the full code, just tell me whether or not the student says that the main reason the code is broken is because 'the chunks could contain the same data or be overlapping' or something like this. Saying 'a word might be split in half' is wrong. Saying 'you might miss a word' is also wrong. Here is their answer:

{response}

Tell me either 'The student passes' or 'The student fails'."""
    
    # Get API token from environment
    token = os.getenv("LLMFOUNDRY_TOKEN")
    if not token:
        return {
            'pass': False,
            'score': 0,
            'reason': 'LLMFOUNDRY_TOKEN environment variable not set'
        }
    
    # Prepare the API request
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": eval_prompt}]
    }
    
    # Make the API call using curl
    curl_command = [
        'curl', '-X', 'POST', 
        'https://llmfoundry.straive.com/openai/v1/chat/completions',
        '-H', f'Authorization: Bearer {token}:my-test-project',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload)
    ]
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'API call failed: {result.stderr}'
            }
        
        # Parse the response
        api_response = json.loads(result.stdout)
        eval_result = api_response['choices'][0]['message']['content'].strip()
        
        # Echo the evaluation result
        print('ECHOING:', eval_result)
        
        # Check if student passes
        passes = "student passes" in eval_result.lower()
        
        return {
            'pass': passes,
            'score': 1.0 if passes else 0.0,
            'reason': f'Evaluator response: {eval_result}'
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
        
        
