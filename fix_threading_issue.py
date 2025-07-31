import subprocess
import json
import os

def assert_identifies_pickling_error(response, context=None):
    """
    Evaluates if the response correctly identifies that create_speech_file function 
    is raising an unpicklable exception.
    """
    
    # Prepare the evaluation prompt
    evaluation_prompt = f"""I showed a student some code with a bug. I then tested their understanding by asking them to explain how to fix the bug. I'm going to show you their answer, I want you to evaluate whether or not their answer says something to the effect of "The function create_speech_file is raising an exception that can not be pickled.". Do not judge their reasoning, or if they know how to fix it, just tell me if they correctly identified that there is a crash in the create_speech_file function.

Student Answer: "{response}"

Think out loud then answer either "The student passes" or "The student fails"."""

    # Get the API token from environment
    token = os.getenv("LLMFOUNDRY_TOKEN")
    if not token:
        return {
            'pass': False,
            'score': 0,
            'reason': 'LLMFOUNDRY_TOKEN environment variable not set'
        }

    # Prepare the curl command
    curl_cmd = [
        'curl', '-X', 'POST', 
        'https://llmfoundry.straive.com/openai/v1/chat/completions',
        '-H', f'Authorization: Bearer {token}:my-test-project',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": evaluation_prompt}]
        })
    ]
    
    try:
        # Execute the curl command
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Curl command failed: {result.stderr}'
            }
        
        # Parse the response
        response_data = json.loads(result.stdout)
        evaluation_response = response_data['choices'][0]['message']['content']
        
        # Check if the evaluation contains "student passes"
        passes = "student passes" in evaluation_response.lower()
        
        return {
            'pass': passes,
            'score': 1 if passes else 0,
            'reason': f'Evaluation result: {evaluation_response}'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'LLM evaluation timed out'
        }
    except json.JSONDecodeError as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Failed to parse LLM response: {e}'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Unexpected error: {e}'
        }