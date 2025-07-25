import re
import subprocess
import tempfile
import os
from PIL import Image
import io
import platform
import sys

def assert_flag_draw_bmp(response, context=None):
    """
    Evaluates if the response contains C code that generates an American flag BMP image.
    
    Args:
        response: The LLM response containing C code
        context: Additional context (unused)
    
    Returns:
        dict: Pass/fail result with details
    """
    
    try:
        # Step 1: Extract C code from response
        code = extract_c_code(response)
        if not code:
            return {
                "pass": False,
                "score": 0,
                "reason": "No C code found in response"
            }
        
        # Step 2: Compile and run C code to get BMP output
        bmp_bytes, compile_error, run_error = compile_and_run_c_code(code)
        if not bmp_bytes:
            reason = "Failed to compile or run C code"
            if compile_error:
                reason += f"\nCompilation error: {compile_error}"
            if run_error:
                reason += f"\nExecution error: {run_error}"
            return {
                "pass": False,
                "score": 0,
                "reason": reason
            }
        
        # Step 3: Validate BMP format and check if it's an image
        try:
            img = Image.open(io.BytesIO(bmp_bytes))
            img.verify()  # Verify it's a valid image
        except Exception as e:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Generated output is not a valid BMP image: {str(e)}"
            }
        
        # Step 4: Check if the image appears to be an American flag
        # Since we're avoiding LLM calls, we'll do basic validation:
        # - Check if it's a valid BMP
        # - Has reasonable dimensions for a flag
        # - Has appropriate color patterns (red, white, blue dominant)
        img = Image.open(io.BytesIO(bmp_bytes))
        width, height = img.size
        
        # Basic flag dimension check (width should be roughly 1.9x height for US flag)
        if width < 50 or height < 25:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Image dimensions too small to be a recognizable flag: {width}x{height}"
            }
        
        # Check for presence of red, white, and blue colors
        colors = img.getcolors(maxcolors=256*256*256)
        if not colors:
            return {
                "pass": False,
                "score": 0,
                "reason": "Could not analyze image colors"
            }
        
        # Look for flag-like color patterns (red, white, blue dominance)
        has_red = has_white = has_blue = False
        for count, color in colors:
            if isinstance(color, tuple) and len(color) >= 3:
                r, g, b = color[:3]
                # Check for red-ish colors
                if r > 150 and g < 100 and b < 100:
                    has_red = True
                # Check for white-ish colors
                if r > 200 and g > 200 and b > 200:
                    has_white = True
                # Check for blue-ish colors
                if r < 100 and g < 100 and b > 150:
                    has_blue = True
        
        if has_red and has_white and has_blue:
            return {
                "pass": True,
                "score": 1,
                "reason": "Successfully generated BMP image with flag-like colors (red, white, blue)"
            }
        else:
            missing_colors = []
            if not has_red: missing_colors.append("red")
            if not has_white: missing_colors.append("white") 
            if not has_blue: missing_colors.append("blue")
            
            return {
                "pass": False,
                "score": 0.5,
                "reason": f"Generated valid BMP but missing typical flag colors: {', '.join(missing_colors)}"
            }
            
    except Exception as e:
        import traceback
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during evaluation: {str(e)}\nTraceback: {traceback.format_exc()}"
        }

def extract_c_code(response):
    """Extract C code from the LLM response, keeping main function."""
    
    # Remove non-ASCII characters to prevent encoding issues
    response = re.sub(r'[^\x00-\x7F]+', '', response)
    
    # Remove language specifiers from code blocks
    response = re.sub('```[a-z]*', '```', response)
    
    # Try to extract from code blocks first
    if response.count("```") >= 2:
        code = response.split("```")[1]
        return code.strip()
    
    # If no code blocks, assume the entire response is code
    return response.strip()

def compile_and_run_c_code(code):
    """Compile and run C code, returning stdout as bytes and any errors."""
    
    # Determine system platform
    is_windows = platform.system() == "Windows"
    exe_extension = ".exe" if is_windows else ""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        c_file = os.path.join(temp_dir, "main.c")
        exe_file = os.path.join(temp_dir, f"main{exe_extension}")
        
        compile_error = None
        run_error = None
        
        try:
            # Write C code to file with UTF-8 encoding
            with open(c_file, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(code)
            
            # Define compiler command (MinGW for Windows if using it)
            compiler = "gcc"
            if is_windows:
                # Try common MinGW locations
                mingw_paths = [
                    r"C:\MinGW\bin\gcc.exe",
                    r"C:\msys64\mingw64\bin\gcc.exe",
                    r"C:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\gcc.exe"
                ]
                for path in mingw_paths:
                    if os.path.exists(path):
                        compiler = path
                        break
            
            # Compile with gcc
            compile_cmd = [compiler, "-o", exe_file, c_file, "-lm"]
            print(f"Compiling with: {' '.join(compile_cmd)}")
            
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                compile_error = compile_result.stderr
                return None, compile_error, None
            
            # Run the executable and capture stdout as bytes
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                timeout=30
            )
            
            if run_result.returncode != 0:
                run_error = run_result.stderr.decode('utf-8', errors='ignore')
                return None, None, run_error
            
            return run_result.stdout, None, None
            
        except subprocess.TimeoutExpired:
            return None, None, "Code execution timed out"
        except Exception as e:
            import traceback
            error_msg = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
            return None, None, error_msg