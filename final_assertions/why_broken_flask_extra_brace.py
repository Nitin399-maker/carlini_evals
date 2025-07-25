import subprocess
import json
import os
import sys
import io


# Ensure stdout/stderr are safe for UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def assert_identifies_extra_brace(response, context=None):
    evaluation_prompt = f"""I asked a question about why some code was incorrect. The answer is \"because the input contains an extra curly brace\". Does this student answer say that?\n\n This is the student response:{response}\n\nAnswer either 'The student passes' or 'The student fails."""
    
    curl_command = [
        'curl', '-X', 'POST',
        'https://llmfoundry.straive.com/openai/v1/chat/completions',
        '-H', f'Authorization: Bearer {os.getenv("LLMFOUNDRY_TOKEN")}:my-test-project',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": evaluation_prompt}]
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
        success = "The student passes." in llm_evaluation

        return {
            "pass": success,
            "score": 1.0 if success else 0.0,
            "reason": "The student passes" if success else "The student fails."
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
