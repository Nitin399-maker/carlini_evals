import subprocess
import json
import os
import sys
import io

# Ensure stdout/stderr are safe for UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def assert_aws_security_issue(response, context=None):
    """
    Evaluates if the response identifies overly permissive IPv6 ranges in AWS Lambda code.
    """

    evaluation_prompt = """Below is a software engineer's answer to a request to find an issue with the following code: {}

Does the engineer mention overly permissive IPv6 ranges? Think out loud, and then end your answer with either the string "The issue is found" or "The issue is not found"."""

    formatted_prompt = evaluation_prompt.format(response)

    curl_command = [
        'curl', '-X', 'POST',
        'https://llmfoundry.straive.com/openai/v1/chat/completions',
        '-H', f'Authorization: Bearer {os.getenv("LLMFOUNDRY_TOKEN")}:my-test-project',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": formatted_prompt}]
        })
    ]

    try:
        result = subprocess.run(
            curl_command,
            capture_output=True,
            text=True,
            check=True
        )

        stdout = result.stdout or ""
        if not stdout.strip():
            raise RuntimeError("Empty response from LLM API")

        try:
            llm_response_data = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON: {e}\nRaw output:\n{stdout}")

        llm_evaluation = llm_response_data['choices'][0]['message']['content']
        success = "The issue is found" in llm_evaluation

        return {
            "pass": success,
            "score": 1.0 if success else 0.0,
            "reason": "The issue is found" if success else "The issue is not found"
        }

    except subprocess.CalledProcessError as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Subprocess call failed: {e.stderr}"
        }

    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error during evaluation: {str(e)}"
        }
