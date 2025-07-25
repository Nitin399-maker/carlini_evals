import re
import subprocess
import tempfile
import os

def check_fix_json_function(response, context=None):
    """
    Promptfoo assertion to test if the model can write a valid fix_json function
    that fixes Python-style malformed JSON and converts it into proper JSON.
    """
    try:
        # Extract code from model response
        code = extract_code_from_response(response)
        if not code:
            return {"pass": False, "score": 0, "reason": "No code found in response"}

        # Append test cases (must exactly match expected output)
        test_case = '''
result1 = fix_json('{"a": 5, "b": [3, 4]}')
print(result1)

result2 = fix_json("{'a': 5.0, 'b': (True, 4)}")
print(result2)

result3 = fix_json("{'True': False, 'b()': (3, 4), \\"c'\\": []}")
print(result3)
'''

        # Full code = function + test cases
        full_code = code + "\n\n" + test_case
        output = run_python_code(full_code)

        if output is None:
            return {"pass": False, "score": 0, "reason": "Code execution failed"}

        expected_answer = '''{"a": 5, "b": [3, 4]}
{"a": 5.0, "b": [true, 4]}
{"True": false, "b()": [3, 4], "c'": []}'''

        cleaned_output = output.strip().replace('\r\n', '\n').replace('\r', '\n')
        if cleaned_output == expected_answer:
            return {"pass": True, "score": 1, "reason": "All test cases passed"}
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Expected output not found.\nExpected:\n{expected_answer}\nGot:\n{cleaned_output}"
            }

    except Exception as e:
        return {"pass": False, "score": 0, "reason": f"Error during evaluation: {str(e)}"}


def extract_code_from_response(response):
    """
    Extracts Python code from markdown-style code blocks in the response.
    """
    response = re.sub(r'```[a-zA-Z]*\n', '```', response)
    if "```" in response:
        parts = response.split("```")
        if len(parts) >= 3:
            return parts[1].strip()
    return response.strip() if response.strip() else None


def run_python_code(code):
    """
    Runs the given Python code and returns stdout, or None if error occurs.
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )

        os.unlink(temp_file)

        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None
