import subprocess
import json
import os

def get_assertion(response, context=None):
    """
    Evaluates if the response correctly identifies that the code calculates the first 20 primes.
    """
    eval_prompt = (
        "I showed a student some code that calculates 20 primes. I then tested their "
        "understanding by asking them to explain it to me. I'm going to show you their "
        "answer, I want you to evaluate whether or not their answer says something to "
        "the effect of \"it calculates the first 20 primes\". Do not judge their "
        "reasoning, just tell me if they got it right.\n"
        f"Student Answer: \"{response}\"\n\n"
        "Think out loud then answer either \"The student passes\" or \"The student fails\"."
    )

    curl_command = [
        "curl", "-X", "POST",
        "https://llmfoundry.straive.com/openai/v1/chat/completions",
        "-H", f'Authorization: Bearer {os.getenv("LLMFOUNDRY_TOKEN")}:my-test-project',
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": eval_prompt}]
        })
    ]

    try:
        result = subprocess.run(curl_command, capture_output=True, check=True)
        stdout_text = result.stdout.decode('utf-8', errors='replace') if isinstance(result.stdout, bytes) else result.stdout

        if not stdout_text:
            return {
                "pass": False,
                "score": 0,
                "reason": "Empty response from LLM API. Check token or network issue."
            }

        try:
            api_response = json.loads(stdout_text)
        except json.JSONDecodeError as e:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Failed to parse JSON: {e}\nRaw Output: {stdout_text}"
            }

        eval_output = api_response["choices"][0]["message"]["content"]
        passes = "student passes" in eval_output.lower()

        return {
            "pass": passes,
            "score": 1 if passes else 0,
            "reason": f"Evaluator output: {eval_output}"
        }

    except subprocess.CalledProcessError as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Subprocess error: {e}\nStderr: {e.stderr}"
        }
