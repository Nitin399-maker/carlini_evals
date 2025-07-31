import re
import subprocess
import tempfile
import os
import ast

def evaluate_transcript_merge_function(response,context=None):
    """
    Evaluates if the LLM correctly implemented a merge function for transcript segments.
    The function should parse transcript data and merge words into sentences ending with periods.
    
    Args:
        response: The LLM response with the implementation
        
    Returns:
        dict: Result with pass/fail status and details
    """
    # Extract code from the response
    code = extract_code(response)
    if not code:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Could not extract valid Python code from the response"
        }
    
    # The required helper function for parsing transcripts
    helper_code = """
import re
from datetime import timedelta

def parse_transcript(content):
    transcript_segments = []
    pattern = r'\\[(\\d{2}:\\d{2}:\\d{2}\\.\\d{3}) --> (\\d{2}:\\d{2}:\\d{2}\\.\\d{3})\\]  (.*)'
    matches = re.findall(pattern, content)
    for start_time, end_time, text in matches:
        start_seconds = timedelta(hours=int(start_time[:2]), minutes=int(start_time[3:5]), seconds=int(start_time[6:8]), milliseconds=int(start_time[9:])).total_seconds()
        end_seconds = timedelta(hours=int(end_time[:2]), minutes=int(end_time[3:5]), seconds=int(end_time[6:8]), milliseconds=int(end_time[9:])).total_seconds()
        transcript_segments.append((start_seconds, end_seconds, text))
    return transcript_segments
"""
    
    # Test case to run the merge function
    test_case = """
print(merge("[00:00:14.240 --> 00:00:14.420]   the\\n[00:00:14.420 --> 00:00:14.860]   robust\\n[00:00:14.860 --> 00:00:15.020]  ness\\n[00:00:15.020 --> 00:00:15.140]   of\\n[00:00:15.140 --> 00:00:15.500]   neural\\n[00:00:15.500 --> 00:00:15.870]   networks\\n[00:00:15.870 --> 00:00:16.200]  .\\n[00:00:16.200 --> 00:00:16.410]   And\\n[00:00:16.410 --> 00:00:16.700]   this\\n[00:00:16.700 --> 00:00:16.840]   is\\n[00:00:16.840 --> 00:00:17.200]   joint\\n"))
"""
    
    # Run the code with the test case
    output = run_python_code(helper_code + "\n" + code + "\n" + test_case)
    print("Output from merge function:", output.strip())
    # Check if the output is correct
    expected_output = "[' the robustness of neural networks.', ' And this is joint']"
    
    # Try to normalize the output and expected output for comparison
    normalized_output = normalize_list_output(output)
    normalized_expected = normalize_list_output(expected_output)
    
    # Check if the normalized outputs match
    outputs_match = normalized_output == normalized_expected
    
    if outputs_match:
        reason = "Merge function correctly combines transcript words into sentences"
    else:
        reason = f"Merge function output doesn't match expected. Got: {output.strip()}, Expected: {expected_output}"
    print(reason)
    return {
        "pass": outputs_match,
        "score": 1.0 if outputs_match else 0.0,
        "reason": reason,

    }

def extract_code(response):
    """Extract Python code from the LLM response"""
    # Try to extract code from markdown code blocks
    pattern = r"```(?:python)?(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL)
    
    if matches:
        # Return the content of the first code block
        return matches[0].strip()
    
    # If no code blocks, try to extract the function definition
    function_pattern = r"(def\s+merge\s*\(.*?\).*?)(?:\n\n|\Z)"
    function_match = re.search(function_pattern, response, re.DOTALL)
    if function_match:
        return function_match.group(1)
    
    # If still no match, look for any function definition
    any_function_pattern = r"(def\s+\w+\s*\(.*?\).*?)(?:\n\n|\Z)"
    any_function_match = re.search(any_function_pattern, response, re.DOTALL)
    if any_function_match:
        return any_function_match.group(1)
    
    return None

def run_python_code(code):
    """Run Python code and return the output"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(code.encode('utf-8'))
        
        # Run the Python code
        try:
            process = subprocess.run(
                ['python', temp_file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Combine stdout and stderr for comprehensive output
            output = process.stdout
            if process.stderr:
                output += "\nERROR: " + process.stderr
                
            return output
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        return f"Error running Python code: {str(e)}"

def normalize_list_output(output_str):
    """Normalize a string representation of a list for comparison"""
    try:
        # Try to evaluate the string as a Python expression (list)
        parsed_list = ast.literal_eval(output_str.strip())
        if isinstance(parsed_list, list):
            # Sort the list for consistent comparison
            return sorted(parsed_list)
    except (SyntaxError, ValueError):
        # If it's not a valid Python expression, fall back to basic normalization
        pass
    
    # Basic normalization: remove spaces, quotes, and sort
    normalized = output_str.replace(" ", "").replace("'", "").replace('"', "")
    if normalized.startswith("[") and normalized.endswith("]"):
        items = normalized[1:-1].split(",")
        return sorted(items)
    
    return output_str.strip()

