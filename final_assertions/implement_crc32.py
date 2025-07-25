import subprocess
import tempfile
import os
import re
import zlib

def extract_code(text, keep_main=True):
    """Extract code from LLM response, optionally keeping main function"""
    # Remove language specifiers from code blocks
    text = re.sub(r'```[a-z]*', '```', text)
    
    if "```" in text and text.count("```") >= 2:
        # Extract code from markdown code block
        code = text.split("```")[1]
    else:
        # Use entire response as code
        code = text
    
    return code.strip()

def compile_and_run_c(code):
    """Compile and run C code, return output"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write C code to file
        c_file = os.path.join(temp_dir, "main.c")
        with open(c_file, 'w') as f:
            f.write(code)
        
        # Compile
        exe_file = os.path.join(temp_dir, "a.out")
        compile_result = subprocess.run(
            ["gcc", "-o", exe_file, c_file, "-lm"],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            raise Exception(f"Compilation failed: {compile_result.stderr}")
        
        # Run executable
        run_result = subprocess.run(
            [exe_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if run_result.returncode != 0:
            raise Exception(f"Execution failed: {run_result.stderr}")
        
        return run_result.stdout

def check_output_contains_substring(output, expected, case_insensitive=True):
    """Check if output contains expected substring"""
    if case_insensitive:
        return expected.lower() in output.lower()
    else:
        return expected in output

def assert_crc32_implementation(response, context=None):
    """
    Promptfoo assertion to test CRC32 implementation in C
    """
    try:
        # Calculate expected CRC32 hash
        expected_hash = "%x" % zlib.crc32(b'correct horse battery staple')
        
        # Extract C code from response
        code = extract_code(response, keep_main=True)
        
        # Compile and run the C code
        output = compile_and_run_c(code)
        
        # Check if output contains expected hash (case insensitive)
        contains_hash = check_output_contains_substring(output, expected_hash, case_insensitive=True)
        
        return {
            "pass": contains_hash,
            "score": 1.0 if contains_hash else 0.0,
            "reason": f"Expected hash '{expected_hash}' {'found' if contains_hash else 'not found'} in output: '{output.strip()}'"
        }
        
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error during evaluation: {str(e)}"
        }