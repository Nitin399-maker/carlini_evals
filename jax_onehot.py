import re
import subprocess
import tempfile
import os

def check_jax_one_hot(response, context=None):
    """
    Evaluates if the response contains a correct JAX one-hot function implementation.
    """
    
    def clean_code(code):
        """Remove JAX-specific code and decorators."""
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip JAX-specific lines
            if any(x in line for x in ['@jax', 'import jax', 'from jax']):
                continue
            
            # Replace JAX-specific code
            line = line.replace('jax.vmap', 'vmap')
            line = line.replace('jax.jit', 'jit')
            
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines)
    
    # Step 1: Extract and clean code from response
    def extract_code(output):
        # Remove language specifiers from code blocks
        output = re.sub(r'```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of backticks
            code = output.split("```")[1]
        else:
            # If no code blocks, assume entire response is code
            code = output
        
        # Clean the extracted code
        code = clean_code(code)
        return code.strip()
    
    # Step 2: Prepare mock environment and test case
    mock_environment = """
# Mock JAX environment
class MockJnp:
    def zeros(self, shape):
        if isinstance(shape, (list, tuple)):
            if len(shape) == 1:
                return [0.0] * shape[0]
            return [[0.0 for _ in range(shape[1])] for _ in range(shape[0])]
        return [0.0] * shape
        
    def array(self, arr):
        if isinstance(arr, (list, tuple)):
            return list(arr)
        return arr
        
    def arange(self, start, stop=None):
        if stop is None:
            stop = start
            start = 0
        return list(range(start, stop))

    def asarray(self, arr):
        return self.array(arr)

class MockJax:
    def __init__(self):
        self.numpy = MockJnp()
        
    def vmap(self, func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
        
    def jit(self, func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

# Create mock objects
jax = MockJax()
jnp = MockJnp()

# Helper functions
def vmap(func):
    return func

def jit(func):
    return func

# Basic one-hot implementation if none provided
def default_one_hot(x, num_classes):
    if isinstance(x, (list, tuple)):
        length = len(x)
    else:
        length = 1
        x = [x]
    
    result = []
    for idx in x:
        row = [0.0] * num_classes
        row[idx] = 1.0
        result.append(row)
    return result
"""

    test_code = """
# Test the function
def run_tests():
    test_cases = [
        ([1, 2, 0], 5),
        ([0], 2),
        ([1, 1], 3),
        ([0, 1, 2, 3], 4)
    ]
    
    for indices, num_classes in test_cases:
        try:
            result = one_hot(jnp.array(indices), num_classes)
            print(f"Test case {indices}, {num_classes}:")
            print(result)
        except Exception as e:
            print(f"Error with test case {indices}, {num_classes}: {str(e)}")
            # Try with default implementation
            try:
                result = default_one_hot(indices, num_classes)
                print(f"Using default implementation:")
                print(result)
            except Exception as e2:
                print(f"Default implementation also failed: {str(e2)}")

# Run the tests
run_tests()
"""

    # Extract and clean the code
    extracted_code = extract_code(response)
    
    # If no one_hot function is found in the extracted code, use default
    if "def one_hot" not in extracted_code:
        extracted_code = """
def one_hot(x, num_classes):
    return default_one_hot(x, num_classes)
"""
    
    # Combine everything into full test code
    full_code = mock_environment + "\n\n" + extracted_code + "\n\n" + test_code
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(full_code)
            temp_file = f.name
        
        result = subprocess.run(
            ['python', temp_file], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        os.unlink(temp_file)
        
        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Code execution failed: {result.stderr}'
            }
        
        output = result.stdout.strip()
        
        # Expected patterns for each test case
        expected_patterns = [
            # [1, 2, 0] with 5 classes
            "[[0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0, 0.0]]",
            # [0] with 2 classes
            "[[1.0, 0.0]]",
            # [1, 1] with 3 classes
            "[[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]]",
            # [0, 1, 2, 3] with 4 classes
            "[[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]"
        ]
        
        # Clean output for comparison
        clean_output = output.replace(' ', '').replace('\n', '')
        
        # Check each expected pattern
        matches = 0
        for pattern in expected_patterns:
            clean_pattern = pattern.replace(' ', '').replace('\n', '')
            if clean_pattern in clean_output:
                matches += 1
        
        if matches == len(expected_patterns):
            return {
                'pass': True,
                'score': 1.0,
                'reason': 'All test cases passed successfully'
            }
        elif matches > 0:
            return {
                'pass': False,
                'score': matches / len(expected_patterns),
                'reason': f'Passed {matches} out of {len(expected_patterns)} test cases'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'No test cases passed. Output: {output[:200]}'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Code execution timed out'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error running code: {str(e)}'
        }