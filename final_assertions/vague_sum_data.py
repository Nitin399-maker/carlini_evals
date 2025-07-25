import subprocess
import tempfile
import os
import re
import json

def assert_sum_some_data(response, context=None):
    """
    Promptfoo assertion function that:
    1. Extracts code from LLM response
    2. Runs the extracted code with test case
    3. Checks if output contains expected answer
    """
    
    # Test data and expected answer
    data = "QUERY A361\\nFound at: 160392127418\\nNumber of times present: 4\\n\\n\\nFound at: 150158692866\\nNumber of times present: 4\\n\\n\\nFound at: 122340445248\\nNumber of times present: 17\\n\\n\\nFound at: 137248651778\\nNumber of times present: 84\\n\\n\\nFound at: 131891981708\\nNumber of times present: 66\\n\\n\\nQUERY 32B57\\nFound at: 194561247604\\nNumber of times present: 4\\n\\n\\nFound at: 82888490886\\nNumber of times present: 3\\n\\n\\nFound at: 115836535414\\nNumber of times present: 19\\n\\n\\nFound at: 79615924948\\nNumber of times present: 81\\n"
    test_case = f"print(process('{data}'))"
    expected_answer = "{'A361': 175, '32B57': 107}"
    
    # Step 1: Extract code from response
    extracted_code = extract_code_with_main(response)
    if not extracted_code:
        return {
            "pass": False,
            "score": 0,
            "reason": "Failed to extract code from response"
        }
    
    # Clean the code - remove non-ASCII characters
    extracted_code = clean_code(extracted_code)
    
    # Step 2: Run the code with test case
    try:
        output = run_python_code(extracted_code, test_case)
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Failed to execute code: {str(e)}"
        }
    
    # Step 3: Check if output contains expected answer
    if expected_answer in output:
        return {
            "pass": True,
            "score": 1,
            "reason": "Code correctly processes data and returns expected result"
        }
    else:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Expected '{expected_answer}' in output, but got: {output.strip()}"
        }


def clean_code(code):
    """Clean the code by removing non-UTF8 characters and fixing quotes"""
    # Remove or replace non-ASCII characters
    cleaned = ""
    for char in code:
        if ord(char) < 128:
            cleaned += char
        else:
            # Replace with appropriate ASCII equivalent if possible
            if char in '""':  # Smart quotes
                cleaned += '"'
            elif char in '':  # Smart apostrophe
                cleaned += "'"
            elif char in '–—':  # Em/en dash
                cleaned += "-"
            elif char in '…':  # Ellipsis
                cleaned += "..."
            # Skip other non-ASCII characters
    return cleaned


def extract_code_with_main(response):
    """Extract and prepare code for execution with main functionality"""
    
    # First try to extract from code blocks
    code = try_extract_from_blocks(response)
    if code:
        return code
    
    # If no code blocks, try to extract using LLM
    return extract_code_with_llm(response)


def try_extract_from_blocks(output):
    """Try to extract code from markdown code blocks"""
    output = re.sub('```[a-z]*', '```', output)
    if "```" in output and output.count("```") >= 2:
        blocks = output.split("```")
        for i in range(1, len(blocks), 2):
            if blocks[i].strip():
                return blocks[i].strip()
    return None


def extract_code_with_llm(orig_output):
    """Use LLM to extract complete runnable code"""
    import os
    import requests
    
    token = os.getenv('LLMFOUNDRY_TOKEN')
    if not token:
        # Fallback: try to extract code without LLM
        return orig_output
    
    prompt = f"Take the below answer to my programming question and return just the complete code in a single file so I can copy and paste it into an editor and directly run it. Include any header and main necessary so I can run it by copying this one file. DO NOT MODIFY THE CODE OR WRITE NEW CODE. Here is the code: \n{orig_output}"
    
    try:
        response = requests.post(
            'https://llmfoundry.straive.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {token}:my-test-project',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [{'role': 'user', 'content': prompt}]
            }
        )
        
        if response.status_code == 200:
            llm_response = response.json()['choices'][0]['message']['content']
            return try_extract_from_blocks(llm_response) or llm_response
        else:
            return orig_output
            
    except Exception:
        return orig_output


def run_python_code(code, test_case):
    """Execute Python code with test case using subprocess"""
    
    full_code = code + "\n\n" + test_case
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(full_code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Code execution failed: {result.stderr}")
            
        return result.stdout
        
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)