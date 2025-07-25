import tempfile
import os
import re
import sys
from io import StringIO
import contextlib

def get_assertion(response, context=None):
    # Extract code from response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output:
            return output.split("```")[1]
        else:
            return output
    
    # Check if code is not recursive
    def not_recursive(code):
        return code.count("solve_iterative") == 1

    # Function to run code and capture output
    def run_code(code):
        # Capture stdout
        temp_stdout = StringIO()
        with contextlib.redirect_stdout(temp_stdout):
            try:
                exec(code, {})
                return temp_stdout.getvalue()
            except Exception as e:
                raise RuntimeError(f"Code execution failed: {str(e)}")

    # Test case and expected answer
    test_case = """
import random
mylist = list(range(100))
random.shuffle(mylist)
from functools import lru_cache
@lru_cache(maxsize=None)
def my_solve_dp(graph, lines_left, distance_since_last):
    if len(graph) < lines_left: return 1e9, []
    if lines_left == 0 and len(graph) == 0: return 0, []
    # option 1: don't take the line
    value = (1e9, [])
    if distance_since_last < 10:
        value = min(value, my_solve_dp(graph[1:], lines_left, distance_since_last+1))
    # option 2: take the line
    if lines_left > 0:
        sub, how = my_solve_dp(graph[1:], lines_left-1, 0)
        sub += graph[0] + (distance_since_last-8)**2
        value = min(value, (sub, how + [len(graph)]))
    return value
answer = solve_iterative(tuple(mylist), len(mylist)//8, 4)
print(answer)
"""
    
    expected_answer_code = """
import random
mylist = list(range(100))
random.shuffle(mylist)
from functools import lru_cache
@lru_cache(maxsize=None)
def my_solve_dp(graph, lines_left, distance_since_last):
    if len(graph) < lines_left: return 1e9, []
    if lines_left == 0 and len(graph) == 0: return 0, []
    # option 1: don't take the line
    value = (1e9, [])
    if distance_since_last < 10:
        value = min(value, my_solve_dp(graph[1:], lines_left, distance_since_last+1))
    # option 2: take the line
    if lines_left > 0:
        sub, how = my_solve_dp(graph[1:], lines_left-1, 0)
        sub += graph[0] + (distance_since_last-8)**2
        value = min(value, (sub, how + [len(graph)]))
    return value
expected = my_solve_dp(tuple(mylist), len(mylist)//8, 4)
print(expected)
"""
    
    try:
        # Extract code from response
        code = extract_code(response)
        
        # Check if not recursive
        if not not_recursive(code):
            return {
                "pass": False,
                "score": 0,
                "reason": "Code is recursive (solve_iterative appears more than once or not at all)"
            }
        
        # Run the extracted code with test case
        try:
            actual_output = run_code(code + "\n\n" + test_case)
            actual_output = actual_output.strip()
        except Exception as e:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Code execution failed: {str(e)}"
            }
        
        # Get expected answer
        try:
            expected_output = run_code(expected_answer_code)
            expected_output = expected_output.strip()
        except Exception as e:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Expected answer calculation failed: {str(e)}"
            }
        
        # Compare outputs
        if actual_output == expected_output:
            return {
                "pass": True,
                "score": 1,
                "reason": "Code passes all tests"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Output mismatch. Expected: {expected_output}, Got: {actual_output}"
            }
            
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during evaluation: {str(e)}"
        }