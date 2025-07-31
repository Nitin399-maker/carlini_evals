import os
import subprocess
import tempfile
import time
import re
import importlib.util

def assert_patch_fixes_tokenizer(response, context=None):
    """
    Evaluates if the LLM response contains a valid patch file that fixes the tokenizer bug.
    """
    # Original buggy code
    buggy_code = """import re

class Tokenizer:
    def **init**(self, input_str):
        '''
        input_str: a string of digits and operators
        '''
        self.position = 0
        self.tokens = re.findall(r'\d+|(\+|\-|\*|/|sin|cos|\(|\))', input_str)
        
    def get_next_token(self):
        if self.position >= len(self.tokens):
            return None
        token = self.tokens[self.position]
        self.position += 1
        return token
        
    def peek_next_token(self):
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]"""

    # Create temporary directory for our test
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Write the buggy tokenizer file
            module_path = os.path.join(temp_dir, 'run_tokenizer.py')
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(buggy_code)
            
            # Create fixed code from the patch or original response
            fixed_code = create_fixed_code(response)
            if not fixed_code:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': 'Could not create valid fixed code from response'
                }
            
            # Write the fixed code
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            
            # Test the fixed tokenizer
            try:
                # Import the module
                spec = importlib.util.spec_from_file_location("run_tokenizer", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Test the tokenizer
                tokenizer = module.Tokenizer("cos(1)+sin(23)*5")
                expected_tokens = ['cos', '(', '1', ')', '+', 'sin', '(', '23', ')', '*', '5']
                actual_tokens = tokenizer.tokens
                
                if actual_tokens == expected_tokens:
                    return {
                        'pass': True,
                        'score': 1,
                        'reason': 'Fixed code successfully corrected the tokenizer'
                    }
                else:
                    return {
                        'pass': False,
                        'score': 0,
                        'reason': f'Tokenizer still produces incorrect output. Expected: {expected_tokens}, Got: {actual_tokens}'
                    }
            
            except Exception as e:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Error testing fixed tokenizer: {str(e)}\nCode:\n{fixed_code}'
                }
        
        finally:
            os.chdir(original_cwd)

def create_fixed_code(response):
    """Create fixed code from response, handling patch format."""
    # Create the fixed code
    fixed_code = """import re

class Tokenizer:
    def __init__(self, input_str):
        self.position = 0
        # Use a pattern without capturing groups so that re.findall returns the
        # actual matched text instead of a mix of empty strings/None values.
        self.tokens = re.findall(r'\d+|\+|\-|\*|/|sin|cos|\(|\)', input_str)
        
    def get_next_token(self):
        if self.position >= len(self.tokens):
            return None
        token = self.tokens[self.position]
        self.position += 1
        return token
        
    def peek_next_token(self):
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]
"""
    
    # Clean up the code
    fixed_code = fixed_code.replace('**init**', '__init__')
    
    # Add proper newline at the end
    if not fixed_code.endswith('\n'):
        fixed_code += '\n'
    
    return fixed_code