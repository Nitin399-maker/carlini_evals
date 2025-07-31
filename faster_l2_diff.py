import re
import subprocess
import tempfile
import os

def assert_fast_l2(response, context=None):
    # Extract code from response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        else:
            return output

    code = extract_code(response)
    
    # Test case and tracer setup
    test_case = """
import numpy as np

if __name__ == "__main__":
    result = diff(np.arange(100).reshape((10, 10)), np.arange(100).reshape((10, 10))).sum()
    print(result)
"""

    tracer = """
import tracemalloc
import numpy as np

if __name__ == "__main__":
    tracemalloc.start()

    snapshot1 = tracemalloc.take_snapshot()
    diff(np.arange(10000).reshape((100, 100)), np.arange(10000).reshape((100, 100)))
    snapshot2 = tracemalloc.take_snapshot()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if peak < 10**6:
        print("Efficient")
"""

    # Run test case
    test_passed = False
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code + "\n" + test_case)
            test_file = f.name
        
        result = subprocess.run(['python', test_file], capture_output=True, text=True, timeout=10)
        test_passed = "1650000" in result.stdout
        os.unlink(test_file)
    except:
        test_passed = False

    # Run tracer
    efficient_passed = False
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code + "\n" + tracer)
            tracer_file = f.name
        
        result = subprocess.run(['python', tracer_file], capture_output=True, text=True, timeout=10)
        efficient_passed = "Efficient" in result.stdout
        os.unlink(tracer_file)
    except:
        efficient_passed = False

    # Check for vectorization (no explicit for loops)
    vectorized_passed = "for " not in code.strip()

    # All conditions must pass
    if test_passed and efficient_passed and vectorized_passed:
        return {
            "pass": True,
            "score": 1.0,
            "reason": "Code passes correctness test, is memory efficient, and is vectorized"
        }
    else:
        reasons = []
        if not test_passed:
            reasons.append("failed correctness test")
        if not efficient_passed:
            reasons.append("not memory efficient")
        if not vectorized_passed:
            reasons.append("not vectorized (contains explicit for loops)")
        
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Code failed: {', '.join(reasons)}"
        }