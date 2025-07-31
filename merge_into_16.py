import subprocess
import tempfile
import os
import re
import random
import shutil

def assert_python_file_merger(response, context=None):
    """
    Evaluates if the model can write a Python script that merges file paths into 16 equal-sized files.
    """
    
    def setup():
        """Create temporary directory structure and test files."""
        temp_dir = tempfile.mkdtemp()
        a_dir = os.path.join(temp_dir, "a")
        os.makedirs(a_dir, exist_ok=True)
        
        files_list_path = os.path.join(temp_dir, "files")
        
        # Create the files list and actual files
        with open(files_list_path, "w", encoding='utf-8') as f:
            for i in range(1000):
                file_path = os.path.join(a_dir, f"file_{i}")
                f.write(f"{file_path}\n")
                
                with open(file_path, "w", encoding='utf-8') as f2:
                    if i < 5:
                        f2.write("x" * random.randint(10000, 30000))
                    else:
                        f2.write("x" * random.randint(1, 1000))
        
        return temp_dir, a_dir, files_list_path
    
    def extract_and_clean_code(response):
        """Extract and clean code from response."""
        # Remove code block markers
        response = re.sub(r'```[a-z]*', '```', response)
        
        # Extract code
        if "```" in response and response.count("```") >= 2:
            code = response.split("```")[1]
        else:
            code = response
            
        # Clean the code
        code = code.strip()
        
        # Replace problematic characters
        replacements = {
            '\u2192': '->',  # Right arrow
            '\u2190': '<-',  # Left arrow
            '\u2018': "'",   # Left single quote
            '\u2019': "'",   # Right single quote
            '\u201c': '"',   # Left double quote
            '\u201d': '"',   # Right double quote
            '\u2013': '-',   # En dash
            '\u2014': '--',  # Em dash
            '\u2026': '...', # Ellipsis
        }
        
        for old, new in replacements.items():
            code = code.replace(old, new)
        
        # Convert to ASCII, replacing any remaining non-ASCII characters
        code = code.encode('ascii', 'replace').decode('ascii')
        
        return code
    
    def test(temp_dir, a_dir):
        """Test if the merged files meet requirements."""
        import numpy as np
        
        # Check if merged files exist and get their sizes
        sz = []
        for i in range(16):
            merged_file = os.path.join(temp_dir, f"merged_{i}")
            if not os.path.exists(merged_file):
                return False
            with open(merged_file, 'r', encoding='utf-8') as f:
                sz.append(len(f.read()))
        
        # Calculate total size before and after
        size_before = sum(os.path.getsize(os.path.join(a_dir, f"file_{i}")) 
                         for i in range(1000))
        size_after = sum(sz)
        
        # Check total size preservation (allowing for newlines)
        if abs(size_before - size_after) > 2000:
            return False
        
        # Check size distribution (should be approximately equal)
        return max(sz) - min(sz) < 200
    
    try:
        # Setup the test environment
        temp_dir, a_dir, files_list_path = setup()
        
        # Extract and clean code from response
        code = extract_and_clean_code(response)
        
        # Modify paths in the code
        code = code.replace("/tmp/files", files_list_path.replace('\\', '\\\\'))
        code = code.replace("/tmp/merged_", 
                          os.path.join(temp_dir, "merged_").replace('\\', '\\\\'))
        
        # Write the code to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', 
                                       delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_script_path = f.name
        
        try:
            # Run the Python script
            result = subprocess.run(
                ['python', temp_script_path],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Script execution failed with error: {result.stderr}'
                }
            
            # Run the test evaluation
            test_result = test(temp_dir, a_dir)
            
            if test_result:
                return {
                    'pass': True,
                    'score': 1,
                    'reason': 'Successfully created 16 merged files with approximately equal sizes'
                }
            else:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': 'Merged files do not meet size distribution requirements'
                }
                
        finally:
            # Clean up the temporary script
            try:
                if os.path.exists(temp_script_path):
                    os.unlink(temp_script_path)
            except:
                pass
            
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Script execution timed out'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error during evaluation: {str(e)}'
        }
    finally:
        # Clean up temporary directory
        try:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
