import re
import subprocess
import tempfile
import os
import time
import json
import base64
import sys
import platform

def check_html_webgl_house(response, context=None):
    """
    Evaluates if the response contains HTML with WebGL code that draws a house with chimney.
    Returns a score between 0 and 1.
    """
    
    # Step 1: Extract HTML/JavaScript code from response
    code = extract_code(response)
    if not code:
        return {"pass": False, "score": 0, "reason": "No code found in response"}
    
    # Step 2: Check that it doesn't use THREE.js (should be raw WebGL)
    if "THREE." in code:
        return {"pass": False, "score": 0, "reason": "Code uses THREE.js instead of raw WebGL"}
    
    # Step 3: Check if code contains key WebGL elements
    webgl_keywords = ["WebGLRenderingContext", "createShader", "createProgram", "drawArrays", "drawElements"]
    webgl_score = sum(1 for keyword in webgl_keywords if keyword in code) / len(webgl_keywords)
    
    # Step 4: Check for house-related patterns in the code
    house_patterns = [
        (r'triangle|rect|square|shape', 'basic shapes'),
        (r'house|home|building|structure', 'house reference'),
        (r'roof|chimney|window|door', 'house features'),
        (r'gl\.drawArrays|gl\.drawElements', 'drawing commands')
    ]
    
    house_matches = []
    for pattern, description in house_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            house_matches.append(description)
    
    house_score = len(house_matches) / len(house_patterns)
    
    # Step 5: Try to take screenshot if possible
    screenshot_data = None
    vision_description = "No screenshot analysis available"
    
    try:
        screenshot_data = take_screenshot(code)
        if screenshot_data:
            # Try to get vision description if we have API access
            if os.getenv("LLMFOUNDRY_TOKEN"):
                try:
                    vision_description = get_vision_description(screenshot_data)
                except Exception as e:
                    vision_description = f"Vision API error: {str(e)}"
            else:
                vision_description = "Screenshot taken but no API token for vision analysis"
        else:
            vision_description = "Failed to take screenshot"
    except Exception as e:
        vision_description = f"Screenshot error: {str(e)}"
    
    # Step 6: Final evaluation
    has_house_chimney = False
    
    if screenshot_data and os.getenv("LLMFOUNDRY_TOKEN"):
        try:
            has_house_chimney = check_for_house_chimney(vision_description)
        except Exception:
            has_house_chimney = False
    
    # Calculate final score
    # If we have vision confirmation, prioritize that
    if has_house_chimney:
        final_score = 1.0
        reason = f"Vision confirms house with chimney. Description: {vision_description}"
    else:
        # Combine code analysis with partial vision results
        code_analysis_score = (webgl_score + house_score) / 2
        final_score = min(0.8, code_analysis_score)  # Cap at 0.8 without visual confirmation
        
        if final_score > 0.5:
            reason = f"Code appears to draw a house with WebGL (score: {final_score:.2f}). Found: {', '.join(house_matches)}. {vision_description}"
        else:
            reason = f"Code may not draw a house with chimney (score: {final_score:.2f}). Missing elements. {vision_description}"
    
    return {
        "pass": final_score >= 0.7,
        "score": final_score,
        "reason": reason
    }

def extract_code(response):
    """Extract HTML/JavaScript code from the response"""
    # Remove language specifiers from code blocks
    response = re.sub(r'```[a-zA-Z]*', '```', response)
    
    if "```" in response and response.count("```") >= 2:
        # Extract code between first pair of ```
        parts = response.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    
    # If no code blocks, assume entire response is code
    return response.strip()

def take_screenshot(html_code):
    """Try multiple methods to take a screenshot of the HTML code"""
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_code)
        html_path = f.name
    
    screenshot_data = None
    error_messages = []
    
    try:
        # Method 1: Try Chrome headless
        if screenshot_data is None:
            try:
                screenshot_data = try_chrome_screenshot(html_path)
            except Exception as e:
                error_messages.append(f"Chrome screenshot failed: {str(e)}")
        
        # Method 2: Try Firefox headless if available
        if screenshot_data is None:
            try:
                screenshot_data = try_firefox_screenshot(html_path)
            except Exception as e:
                error_messages.append(f"Firefox screenshot failed: {str(e)}")
        
        # Method 3: Try wkhtmltoimage if available
        if screenshot_data is None:
            try:
                screenshot_data = try_wkhtmltoimage(html_path)
            except Exception as e:
                error_messages.append(f"wkhtmltoimage failed: {str(e)}")
        
        # If all methods failed, create a simple text file with the code for analysis
        if screenshot_data is None:
            dummy_image = create_dummy_image(html_code)
            if dummy_image:
                screenshot_data = dummy_image
                error_messages.append("Using dummy image with code text")
        
        return screenshot_data
            
    except Exception as e:
        error_messages.append(f"Screenshot error: {str(e)}")
        return None
    finally:
        # Cleanup HTML file
        if os.path.exists(html_path):
            try:
                os.unlink(html_path)
            except Exception:
                pass

def try_chrome_screenshot(html_path):
    """Try to take a screenshot using Chrome headless"""
    screenshot_path = html_path.replace('.html', '_chrome.png')
    
    # Detect OS and set appropriate Chrome command
    chrome_cmd = 'google-chrome'
    if platform.system() == 'Windows':
        chrome_candidates = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        ]
        for candidate in chrome_candidates:
            if os.path.exists(candidate):
                chrome_cmd = f'"{candidate}"'
                break
    elif platform.system() == 'Darwin':  # macOS
        chrome_cmd = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    # Use Chrome headless to take screenshot
    cmd = [
        chrome_cmd,
        '--headless',
        '--no-sandbox', 
        '--disable-dev-shm-usage',
        '--window-size=1920,1080',
        f'--screenshot={screenshot_path}',
        f'file://{html_path}'
    ]
    
    # Convert string command to list if needed
    if isinstance(chrome_cmd, str) and chrome_cmd.startswith('"'):
        cmd[0] = chrome_cmd
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    # Wait for screenshot to be saved
    time.sleep(2)
    
    # Read screenshot data
    if os.path.exists(screenshot_path):
        with open(screenshot_path, 'rb') as img_file:
            screenshot_data = img_file.read()
        
        # Cleanup
        os.unlink(screenshot_path)
        return screenshot_data
    
    return None

def try_firefox_screenshot(html_path):
    """Try to take a screenshot using Firefox headless"""
    screenshot_path = html_path.replace('.html', '_firefox.png')
    
    # Detect OS and set appropriate Firefox command
    firefox_cmd = 'firefox'
    if platform.system() == 'Windows':
        firefox_candidates = [
            r'C:\Program Files\Mozilla Firefox\firefox.exe',
            r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'
        ]
        for candidate in firefox_candidates:
            if os.path.exists(candidate):
                firefox_cmd = f'"{candidate}"'
                break
    elif platform.system() == 'Darwin':  # macOS
        firefox_cmd = '/Applications/Firefox.app/Contents/MacOS/firefox'
    
    # Use Firefox headless to take screenshot
    cmd = [
        firefox_cmd,
        '--headless',
        '--screenshot', screenshot_path,
        f'file://{html_path}'
    ]
    
    # Convert string command to list if needed
    if isinstance(firefox_cmd, str) and firefox_cmd.startswith('"'):
        cmd[0] = firefox_cmd
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    # Wait for screenshot to be saved
    time.sleep(2)
    
    # Read screenshot data
    if os.path.exists(screenshot_path):
        with open(screenshot_path, 'rb') as img_file:
            screenshot_data = img_file.read()
        
        # Cleanup
        os.unlink(screenshot_path)
        return screenshot_data
    
    return None

def try_wkhtmltoimage(html_path):
    """Try to use wkhtmltoimage for screenshot"""
    screenshot_path = html_path.replace('.html', '_wk.png')
    
    cmd = [
        'wkhtmltoimage',
        '--width', '1920',
        '--height', '1080',
        html_path,
        screenshot_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    # Read screenshot data
    if os.path.exists(screenshot_path):
        with open(screenshot_path, 'rb') as img_file:
            screenshot_data = img_file.read()
        
        # Cleanup
        os.unlink(screenshot_path)
        return screenshot_data
    
    return None

def create_dummy_image(html_code):
    """Create a dummy image with the code text for analysis"""
    try:
        # Extract just the WebGL code for brevity
        webgl_code = extract_webgl_sections(html_code)
        
        # Create a simple text file with base64 encoding to simulate an image
        dummy_text = f"WebGL CODE ANALYSIS:\n\n{webgl_code}"
        return dummy_text.encode('utf-8')
    except Exception:
        return None

def extract_webgl_sections(html_code):
    """Extract just the WebGL-related sections from the HTML code"""
    # Look for script sections with WebGL
    script_pattern = r'<script[^>]*>(.*?)<\/script>'
    scripts = re.findall(script_pattern, html_code, re.DOTALL)
    
    webgl_sections = []
    for script in scripts:
        if any(keyword in script for keyword in ["WebGL", "webgl", "gl.", "createShader", "drawArrays"]):
            webgl_sections.append(script)
    
    return "\n\n".join(webgl_sections) if webgl_sections else html_code[:1000]  # Limit size

def get_vision_description(image_data):
    """Use vision LLM to describe what's in the screenshot"""
    # Check if it's a dummy text image
    if isinstance(image_data, bytes) and image_data.startswith(b"WebGL CODE ANALYSIS"):
        # Return the text directly for code analysis
        return image_data.decode('utf-8')
    
    # Convert image to base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Prepare the API call
    prompt = "This is a screenshot of a webpage that draws something with WebGL. I'm trying to see if it drew a house with a chimney. Describe what is drawn in this image in detail."
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 512
    }
    
    # Make the API call
    cmd = [
        'curl', '-X', 'POST', 
        'https://llmfoundry.straive.com/openai/v1/chat/completions',
        '-H', f'Authorization: Bearer {os.getenv("LLMFOUNDRY_TOKEN")}:my-test-project',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        try:
            response_data = json.loads(result.stdout)
            return response_data['choices'][0]['message']['content']
        except (json.JSONDecodeError, KeyError, IndexError):
            return "Error parsing vision API response"
    else:
        return f"Vision API error: {result.stderr}"

def check_for_house_chimney(description):
    """Check if the description indicates a house with chimney was drawn"""
    # If no API token, do simple keyword analysis
    if not os.getenv("LLMFOUNDRY_TOKEN"):
        house_keywords = ["house", "home", "building", "structure"]
        chimney_keywords = ["chimney", "smoke", "roof"]
        
        has_house = any(keyword in description.lower() for keyword in house_keywords)
        has_chimney = any(keyword in description.lower() for keyword in chimney_keywords)
        
        return has_house and has_chimney
    
    # Otherwise use the API
    prompt = f'Does this answer describe an image showing a house with a chimney? "{description}" Answer "Yes it does" if both a house and a chimney are mentioned or "No it does not" if either is missing.'
    
    payload = {
        "model": "gpt-4o-mini", 
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    # Make the API call
    cmd = [
        'curl', '-X', 'POST',
        'https://llmfoundry.straive.com/openai/v1/chat/completions',
        '-H', f'Authorization: Bearer {os.getenv("LLMFOUNDRY_TOKEN")}:my-test-project',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        try:
            response_data = json.loads(result.stdout)
            answer = response_data['choices'][0]['message']['content']
            # Check if answer contains "es it does" (matching original substring check)
            return "es it does" in answer
        except (json.JSONDecodeError, KeyError, IndexError):
            return False
    else:
        return False