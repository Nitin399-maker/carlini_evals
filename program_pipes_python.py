import re
import subprocess
import tempfile
import os

def assert_dataflow_dsl(response, context=None):
    """
    Evaluates if the model can generate a python program that defines dataflow DSL.
    Expected to work with: Const(2) >> Square() >> Inc() >> Square() >> Square() >> Print()
    Should output 625.
    """

    def extract_code(output):
        # Remove non-ASCII characters
        output = re.sub(r'[^\x00-\x7F]+', '', output)

        # Normalize code block markers like ```python
        output = re.sub(r'```[a-zA-Z]*\n', '```', output)

        # Split and extract code between triple backticks
        parts = output.split("```")
        if len(parts) >= 3:
            code = parts[1]
        else:
            code = output

        # Remove any leftover triple backticks inside the code (causes syntax error)
        code = code.replace("```", "")

        return code.strip()

    code = extract_code(response)

    # Test case to append
    test_case = "Const(2) >> Square() >> Inc() >> Square() >> Square() >> Print()"

    # Final code to be executed
    full_code = code + "\n\n" + test_case + "\n"

    # Validate code before writing
    try:
        compile(full_code, "<string>", "exec")
    except SyntaxError as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Code is invalid Python: {e}"
        }

    # Write to a temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write(full_code)
        temp_file = f.name

    try:
        # Execute the file
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Code execution failed with error:\n{result.stderr.strip()}"
            }

        output = result.stdout.strip()

        if "625" in output:
            return {
                "pass": True,
                "score": 1.0,
                "reason": f"Code executed successfully and produced expected output: {output}"
            }
        else:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Code executed but did not produce expected output '625'. Got: {output}"
            }

    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Code execution timed out"
        }
    except Exception as e:
        import traceback
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Code execution failed: {str(e)}\nTraceback: {traceback.format_exc()}"
        }
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
