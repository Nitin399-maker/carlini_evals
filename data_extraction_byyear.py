import json
import re

def check_json_subset(response, context=None):
    """
    Extracts JSON from LLM response and validates it contains expected year-accuracy pairs.
    """
    expected = {
        "2024": 69.71,
        "2023": 71.07,
        "2022": 65.79,
        "2021": 66.56,
        "2020": 65.87,
        "2019": 59.53,
        "2018": 44.04
    }
    
    def extract_json_from_response(text):
        """Extract JSON from response text, handling code blocks and plain text."""
        # Remove ```json or ``` markers
        text = text.replace("```json", "```")
        
        # If there are code blocks, extract content between them
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                return parts[1].strip()
        
        # Look for JSON-like patterns in the text
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text)
        if matches:
            return matches[0]
            
        return text.strip()
    
    # Extract JSON from response
    json_text = extract_json_from_response(response)
    
    try:
        # Parse the extracted JSON
        parsed_json = json.loads(json_text)
        
        if not isinstance(parsed_json, dict):
            return {
                "pass": False,
                "score": 0.0,
                "reason": "Response is not a JSON object"
            }
        
        # Check if all expected keys are present with correct values
        correct_count = 0
        total_expected = len(expected)
        errors = []
        
        for year, expected_value in expected.items():
            if year in parsed_json:
                actual_value = parsed_json[year]
                if isinstance(actual_value, (int, float)) and abs(actual_value - expected_value) < 0.01:
                    correct_count += 1
                else:
                    errors.append(f"Year {year}: expected {expected_value}, got {actual_value}")
            else:
                errors.append(f"Missing year {year}")
        
        score = correct_count / total_expected
        passed = score >= 1.0  # All must be correct
        
        if passed:
            reason = f"All {total_expected} year-accuracy pairs match expected values"
        else:
            reason = f"Only {correct_count}/{total_expected} correct. Errors: {'; '.join(errors[:3])}"
        
        return {
            "pass": passed,
            "score": score,
            "reason": reason
        }
        
    except json.JSONDecodeError as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error processing response: {str(e)}"
        }