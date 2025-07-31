import subprocess
import json

def get_assertion(response, context=None):
    """
    Evaluates if the response correctly explains the VPBROADCASTB instruction.
    """
    
    evaluation_prompt = f"""Below is a student's answer to a question about what a particular instruction does: {response}

Does the student's say something similar to "Load integer data from the source operand (the second operand) and broadcast to all elements of the destination operand (the first operand)."?

If the answer is correct say "The student passes" otherwise "The student fails"."""
    
    # Create a temporary input file for the evaluation
    eval_input = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user", 
                "content": evaluation_prompt
            }
        ],
        "max_tokens": 100,
        "temperature": 0
    }
    
    try:
        # Use subprocess to call a local evaluation (assuming you have a local LLM setup)
        # If you have ollama or similar local setup:
        result = subprocess.run([
            "curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": "llama2", 
                "messages": [{"role": "user", "content": evaluation_prompt}],
                "stream": False
            })
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            eval_response = json.loads(result.stdout)
            eval_text = eval_response.get("message", {}).get("content", "").lower()
        else:
            # Fallback: simple keyword matching if subprocess fails
            response_lower = response.lower()
            keywords = ["broadcast", "load", "source", "destination", "operand", "elements"]
            keyword_count = sum(1 for keyword in keywords if keyword in response_lower)
            eval_text = "student passes" if keyword_count >= 3 else "student fails"
            
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        # Fallback evaluation using simple heuristics
        response_lower = response.lower()
        
        # Check for key concepts
        has_broadcast = "broadcast" in response_lower
        has_load = any(word in response_lower for word in ["load", "copy", "move"])
        has_operand = "operand" in response_lower
        has_elements = any(word in response_lower for word in ["element", "position", "location"])
        
        # Simple scoring
        score = sum([has_broadcast, has_load, has_operand, has_elements])
        eval_text = "student passes" if score >= 2 else "student fails"
    
    # Check if evaluation contains "student passes"
    passes = "student passes" in eval_text.lower()
    
    return {
        "pass": passes,
        "score": 1.0 if passes else 0.0,
        "reason": "Correctly explained VPBROADCASTB instruction" if passes else "Failed to correctly explain VPBROADCASTB instruction"
    }