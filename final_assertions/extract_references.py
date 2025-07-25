import json
import subprocess
import sys

def assert_paper_titles_extraction(response, context=None):
    """
    Assertion function for Promptfoo to test if the model can extract paper titles from a block of text.
    
    Args:
        response: The LLM response containing extracted paper titles
        context: Additional context (not used in this assertion)
    
    Returns:
        dict: Result with pass/fail status and reasoning
    """
    
    expected_titles = {
        "membership inference attacks against machine learning models",
        "ai2 dolma: 3 trillion token open corpus for language model pretraining", 
        "diffusion art or digital forgery? investigating data replication in diffusion models",
        "ecological methods",
        "llama: open and efficient foundation language models",
        "llama 2: open foundation and fine-tuned chat models",
        "introducing falcon 180b",
        "privacy risk in machine learning: analyzing the connection to overfitting",
        "smooth nonparametric estimation of the quantile function",
        "opt: open pre-trained transformer language models",
        "github copilot research recitation",
        "universal and transferable adversarial attacks on aligned language models",
    }
    
    try:
        # Clean up the response to extract JSON content
        cleaned_response = response.replace("```json", "```")
        
        if "```" not in cleaned_response:
            return {
                "pass": False,
                "score": 0,
                "reason": "No JSON code block found in response"
            }
        
        # Extract content between code blocks
        json_content = cleaned_response.split("```")[1]
        
        # Parse JSON and normalize titles
        extracted_titles = json.loads(json_content)
        normalized_titles = {title.lower().replace(".", "") for title in extracted_titles}
        
        # Check if extracted titles match expected titles
        if normalized_titles == expected_titles:
            return {
                "pass": True,
                "score": 1,
                "reason": f"Successfully extracted all {len(expected_titles)} paper titles correctly"
            }
        else:
            missing = expected_titles - normalized_titles
            extra = normalized_titles - expected_titles
            
            reason_parts = []
            if missing:
                reason_parts.append(f"Missing titles: {list(missing)[:3]}{'...' if len(missing) > 3 else ''}")
            if extra:
                reason_parts.append(f"Extra titles: {list(extra)[:3]}{'...' if len(extra) > 3 else ''}")
            
            return {
                "pass": False,
                "score": 0,
                "reason": "; ".join(reason_parts)
            }
            
    except json.JSONDecodeError as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Failed to parse JSON: {str(e)}"
        }
    except IndexError:
        return {
            "pass": False,
            "score": 0,
            "reason": "Could not extract JSON content from code block"
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Unexpected error: {str(e)}"
        }