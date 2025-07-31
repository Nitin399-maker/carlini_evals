import json
import re
import subprocess
import os

def get_assertion(response, context=None):
    """
    Promptfoo assertion to test if the model can successfully convert unstructured data to JSON.
    Evaluates if the response contains valid JSON with expected model metadata.
    """
    
    expected_data = {
        "Mistral-7B-v0.1": {"size": 7, "dataset": "", "family": "Mistral"},
        "RedPajama-INCITE-7B-Base": {"size": 7, "dataset": "", "family": "RedPajama"},
        "RedPajama-INCITE-Base-3B-v1": {"size": 3, "dataset": "", "family": "RedPajama"},
        "falcon40b": {"size": 40, "dataset": "", "family": "falcon"},
        "falcon7b": {"size": 7, "dataset": "", "family": "falcon"},
        "gpt2-xl": {"size": 1.5, "dataset": "", "family": "gpt2"},
        "llama-65b": {"size": 65, "dataset": "", "family": "llama"},
        "llama-7b": {"size": 7, "dataset": "", "family": "llama"},
        "neo-1.3": {"size": 1.3, "dataset": "", "family": "neo"},
        "neo-2.7": {"size": 2.7, "dataset": "", "family": "neo"},
        "neo-6": {"size": 6, "dataset": "", "family": "neo"},
        "open_llama_3b_v2": {"size": 3, "dataset": "", "family": "open_llama"},
        "open_llama_7b_v2": {"size": 7, "dataset": "", "family": "open_llama"},
        "opt-1.3b": {"size": 1.3, "dataset": "", "family": "opt"},
        "opt-6.7b": {"size": 6.7, "dataset": "", "family": "opt"},
        "pythia-1.4": {"size": 1.4, "dataset": "", "family": "pythia"},
        "pythia-1.4-dedup": {"size": 1.4, "dataset": "", "family": "pythia"},
        "pythia-6.9": {"size": 6.9, "dataset": "", "family": "pythia"},
        "pythia-6.9-dedup": {"size": 6.9, "dataset": "", "family": "pythia"}
    }
    
    def extract_json_from_response(text):
        """Extract JSON from response, handling code blocks and other formatting."""
        # Remove markdown code blocks
        text = text.replace("```json", "```")
        
        # Try to extract from code blocks first
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                json_candidate = parts[1]
                try:
                    return json.loads(json_candidate)
                except json.JSONDecodeError:
                    pass
                
                # Try all odd-indexed parts (content between ```)
                json_parts = parts[1::2]
                combined = "\n".join(json_parts)
                try:
                    return json.loads(combined)
                except json.JSONDecodeError:
                    pass
        
        # Try to find JSON object in the text using regex
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # If we still can't parse, try to use LLM to extract clean JSON
        if "```" not in text or text.count("```") != 2:
            try:
                token = os.getenv("LLMFOUNDRY_TOKEN")
                if not token:
                    return None
                    
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{
                        "role": "user", 
                        "content": f"Take the below answer to my question asking for a JSON output and just return the JSON object directly, with no other description, so I can copy it into an editor directly:\n{text}"
                    }]
                }
                
                result = subprocess.run([
                    'curl', '-X', 'POST', 
                    'https://llmfoundry.straive.com/openai/v1/chat/completions',
                    '-H', f'Authorization: Bearer {token}:my-test-project',
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(payload)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    response_data = json.loads(result.stdout)
                    cleaned_json = response_data['choices'][0]['message']['content']
                    return extract_json_from_response(cleaned_json)
            except:
                pass
        
        # Last attempt: try parsing the entire response as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    
    def check_json_subset(actual, expected):
        """Check if actual JSON contains all expected key-value pairs as subset."""
        if not isinstance(actual, dict) or not isinstance(expected, dict):
            return False
            
        missing_keys = []
        incorrect_values = []
        
        for key, expected_value in expected.items():
            if key not in actual:
                missing_keys.append(key)
                continue
                
            actual_value = actual[key]
            if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                # Recursively check nested dictionaries
                for nested_key, nested_expected in expected_value.items():
                    if nested_key not in actual_value:
                        missing_keys.append(f"{key}.{nested_key}")
                    elif actual_value[nested_key] != nested_expected:
                        incorrect_values.append(f"{key}.{nested_key}: expected {nested_expected}, got {actual_value[nested_key]}")
            elif actual_value != expected_value:
                incorrect_values.append(f"{key}: expected {expected_value}, got {actual_value}")
        
        return len(missing_keys) == 0 and len(incorrect_values) == 0, missing_keys, incorrect_values
    
    # Extract JSON from response
    parsed_json = extract_json_from_response(response)
    
    if parsed_json is None:
        return {
            'pass': False,
            'score': 0.0,
            'reason': 'Failed to extract valid JSON from response'
        }
    
    # Check if parsed JSON matches expected structure
    is_valid, missing_keys, incorrect_values = check_json_subset(parsed_json, expected_data)
    
    if is_valid:
        return {
            'pass': True,
            'score': 1.0,
            'reason': 'Response contains valid JSON with all expected model metadata'
        }
    else:
        error_details = []
        if missing_keys:
            error_details.append(f"Missing keys: {', '.join(missing_keys)}")
        if incorrect_values:
            error_details.append(f"Incorrect values: {', '.join(incorrect_values)}")
            
        return {
            'pass': False,
            'score': 0.0,
            'reason': f"JSON validation failed. {'; '.join(error_details)}"
        }