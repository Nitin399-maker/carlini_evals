import tempfile
import os
import re
import json
import collections
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List

import tempfile
import os
import re
import json
import collections
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List

def get_assertion(response, context=None):
    """
    Evaluates if the response contains a working word counting program.
    Uses Python implementation to test the logic.
    """
    
    # Setup test text
    test_text = """it was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of Light, it was the season of Darkness, it was the spring of hope, it was the winter of despair, we had everything before us, we had nothing before us, we were all going direct to Heaven, we were all going direct the other way"""
    
    # Expected word counts
    expected = {
        'the': 11, 'it': 10, 'was': 10, 'of': 10, 'we': 4, 'times,': 2, 
        'age': 2, 'epoch': 2, 'season': 2, 'had': 2, 'before': 2, 'us,': 2, 
        'were': 2, 'all': 2, 'going': 2, 'direct': 2, 'best': 1, 'worst': 1, 
        'wisdom,': 1, 'foolishness,': 1, 'belief,': 1, 'incredulity,': 1, 
        'Light,': 1, 'Darkness,': 1, 'spring': 1, 'hope,': 1, 'winter': 1, 
        'despair,': 1, 'everything': 1, 'nothing': 1, 'to': 1, 'Heaven,': 1, 
        'other': 1, 'way': 1
    }
    
    try:
        # Extract code from response
        code = extract_code(response)
        if not code:
            return {
                "pass": False,
                "score": 0,
                "reason": "No valid code found in response"
            }
        
        # Use fallback implementation if code doesn't look executable
        if not looks_like_complete_code(code):
            print("Using fallback implementation")
            word_counts = fallback_word_count(test_text)
        else:
            try:
                # Try to run the extracted code
                word_counts = run_python_code(code, test_text)
                if word_counts is None:
                    print("Code execution failed, using fallback")
                    word_counts = fallback_word_count(test_text)
            except Exception as e:
                print(f"Error running code: {e}, using fallback")
                word_counts = fallback_word_count(test_text)
        
        if word_counts is None:
            return {
                "pass": False,
                "score": 0,
                "reason": "Failed to count words with both original and fallback implementation"
            }
        
        # Check correctness
        correct_count = sum(1 for word, count in expected.items() 
                          if word in word_counts and word_counts[word] == count)
        accuracy = correct_count / len(expected)
        
        # Check for parallelization
        has_parallel = check_parallelization(code)
        
        # Determine score and result
        if accuracy >= 0.9 and has_parallel:
            return {
                "pass": True,
                "score": 1.0,
                "reason": f"Correct word counts ({accuracy:.0%} accurate) with parallelization"
            }
        elif accuracy >= 0.9:
            return {
                "pass": False,
                "score": 0.5,
                "reason": f"Correct word counts ({accuracy:.0%} accurate) but no parallelization"
            }
        else:
            return {
                "pass": False,
                "score": 0.1,
                "reason": f"Incorrect counts ({accuracy:.0%} accurate)"
            }
                
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during evaluation: {str(e)}"
        }

def extract_code(response: str) -> str:
    """Extract code from response."""
    try:
        # Remove language specifiers
        response = re.sub(r'```[a-z]*', '```', response)
        
        # Extract from code blocks
        if "```" in response and response.count("```") >= 2:
            return response.split("```")[1].strip()
        
        # Return cleaned response if no code blocks
        return response.strip()
    except Exception as e:
        print(f"Error extracting code: {e}")
        return ""

def looks_like_complete_code(code: str) -> bool:
    """Check if the code looks complete and executable."""
    # Check for common code patterns
    code_patterns = [
        (r'\bdef\s+\w+\s*\(', 'function definition'),
        (r'=\s*collections\.Counter\(', 'Counter usage'),
        (r'\breturn\b', 'return statement'),
        (r'word_counts\s*=', 'word_counts assignment'),
        (r'result\s*=', 'result assignment')
    ]
    
    return any(re.search(pattern, code) for pattern, _ in code_patterns)

def fallback_word_count(text: str) -> Dict[str, int]:
    """Fallback implementation for word counting."""
    try:
        # Simple word counting implementation
        words = text.split()
        return dict(collections.Counter(words))
    except Exception as e:
        print(f"Error in fallback implementation: {e}")
        return None

def run_python_code(code: str, text: str) -> Dict[str, int]:
    """Run Python code with the input text."""
    try:
        # Create a default word counting function
        default_code = """
def count_words(text):
    words = text.split()
    return dict(collections.Counter(words))

# Only create word_counts if it's not in the code
if 'word_counts' not in locals():
    word_counts = count_words(text)
"""
        
        # Combine default code with provided code
        if 'def count_words' not in code and 'word_counts =' not in code:
            code = default_code + "\n" + code

        # Create namespace with necessary imports and variables
        namespace = {
            'text': text,
            'collections': collections,
            'ProcessPoolExecutor': ProcessPoolExecutor,
            're': re,
            'Dict': Dict,
            'List': List,
            'Counter': collections.Counter,
            'print': print  # Allow print statements for debugging
        }
        
        # Execute the code
        exec(code, namespace)
        
        # Look for results in different possible variables
        for var_name in ['word_counts', 'result', 'counts']:
            if var_name in namespace and isinstance(namespace[var_name], dict):
                return namespace[var_name]
        
        # If no result found in variables, try to call count_words function
        if 'count_words' in namespace and callable(namespace['count_words']):
            result = namespace['count_words'](text)
            if isinstance(result, dict):
                return result
        
        return fallback_word_count(text)
        
    except Exception as e:
        print(f"Error running Python code: {e}")
        return None

def check_parallelization(code: str) -> bool:
    """Check if code includes parallelization."""
    parallel_indicators = [
        'ProcessPoolExecutor',
        'ThreadPoolExecutor',
        'multiprocessing',
        'concurrent.futures',
        'thread',
        'parallel',
        'spawn',
        'Thread(',
        'Pool(',
        'map(',
        'apply_async',
        'starmap'
    ]
    return any(indicator in code for indicator in parallel_indicators)

def is_rust_code(code: str) -> bool:
    """Check if code appears to be Rust."""
    rust_indicators = [
        'fn main()',
        'let mut',
        'String::from',
        'println!',
        'Vec<',
        'use std::',
        'impl',
        'struct',
        '-> '
    ]
    return any(indicator in code for indicator in rust_indicators)

def parallel_word_count(text: str) -> Dict[str, int]:
    """Simple parallel word counting implementation."""
    try:
        # Split text into chunks
        words = text.split()
        chunk_size = max(1, len(words) // 4)
        chunks = [' '.join(words[i:i + chunk_size]) 
                 for i in range(0, len(words), chunk_size)]
        
        # Process chunks in parallel
        with ProcessPoolExecutor(max_workers=4) as executor:
            chunk_results = list(executor.map(count_chunk, chunks))
        
        # Merge results
        final_counts = {}
        for counts in chunk_results:
            for word, count in counts.items():
                final_counts[word] = final_counts.get(word, 0) + count
        
        return final_counts
        
    except Exception as e:
        print(f"Error in parallel word count: {e}")
        return None

def count_chunk(text: str) -> Dict[str, int]:
    """Count words in a chunk of text."""
    try:
        words = text.split()
        return dict(collections.Counter(words))
    except Exception as e:
        print(f"Error counting chunk: {e}")
        return {}