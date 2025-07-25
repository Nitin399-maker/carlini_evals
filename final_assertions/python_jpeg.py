import subprocess
import tempfile
import os
import re
import json
import io
from PIL import Image

def assert_red_triangle_gif(response, context=None):
    """
    Evaluates if the response contains code that generates a GIF with a red triangle.
    """
    # Extract code from response
    code = extract_code_from_response(response)
    if not code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'No code found in response'
        }
    
    # Run the Python code and capture output
    try:
        gif_bytes = run_python_code(code)
        if not gif_bytes:
            return {
                'pass': False,
                'score': 0,
                'reason': 'Code execution failed or produced no output'
            }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Code execution error: {str(e)}'
        }
    
    # Analyze the image using PIL instead of LLM
    try:
        has_red, has_triangle = analyze_image(gif_bytes)
        if has_red and has_triangle:
            return {
                'pass': True,
                'score': 1,
                'reason': 'Successfully generated red triangle'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Missing required elements. Has triangle: {has_triangle}, Has red: {has_red}'
            }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Image analysis failed: {str(e)}'
        }

def extract_code_from_response(response):
    """Extract Python code from the response, handling encoding issues."""
    try:
        # Clean the response of non-ASCII characters
        response = response.encode('ascii', 'ignore').decode('ascii')
        
        # Remove language identifiers from code blocks
        response = re.sub(r'```[a-z]*', '```', response)
        
        # Try to extract from code blocks first
        if response.count("```") >= 2:
            code = response.split("```")[1]
            return code.strip()
        
        # If no code blocks, look for Python-like code
        lines = response.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if any(x in line for x in ['import', 'def ', 'class ', 'if __name__']):
                in_code = True
            if in_code:
                code_lines.append(line)
                
        if code_lines:
            return '\n'.join(code_lines)
            
        return response.strip()
        
    except Exception as e:
        print(f"Error extracting code: {str(e)}")
        return response.strip()

def run_python_code(code):
    """Run Python code and capture binary output."""
    try:
        # Create temporary file with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8', errors='ignore') as f:
            f.write("# -*- coding: utf-8 -*-\n")
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                raise Exception(f"Python execution failed: {result.stderr.decode('utf-8', errors='ignore')}")
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except Exception as e:
        raise Exception(f"Error running code: {str(e)}")

def analyze_image(gif_bytes):
    """
    Analyze image using PIL to detect red triangles.
    Returns (has_red, has_triangle) tuple.
    """
    try:
        # Load the GIF
        img = Image.open(io.BytesIO(gif_bytes))
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get image data
        pixels = img.load()
        width, height = img.size
        
        # Check for red pixels
        has_red = False
        red_pixels = []
        
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                # Check if pixel is predominantly red
                if r > 200 and g < 100 and b < 100:
                    has_red = True
                    red_pixels.append((x, y))
        
        # Simple triangle detection: check if red pixels form a triangular pattern
        has_triangle = False
        if len(red_pixels) > 0:
            # Check if red pixels form a roughly triangular shape
            x_coords = [x for x, y in red_pixels]
            y_coords = [y for x, y in red_pixels]
            
            # Calculate bounding box
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            # Check if the distribution of pixels looks triangular
            width = max_x - min_x
            height = max_y - min_y
            
            if width > 0 and height > 0:
                # Simple heuristic: check if pixel count increases/decreases like a triangle
                rows = [0] * (height + 1)
                for x, y in red_pixels:
                    rows[y - min_y] += 1
                
                # Check for triangular pattern in row counts
                max_row = max(rows)
                min_row = min(rows)
                if max_row > min_row * 2:
                    has_triangle = True
        
        return has_red, has_triangle
        
    except Exception as e:
        print(f"Error analyzing image: {str(e)}")
        return False, False