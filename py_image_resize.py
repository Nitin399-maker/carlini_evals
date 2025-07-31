import subprocess
import tempfile
import os
import re
from PIL import Image
import random

def get_assertion(response, context=None):
    temp_file_path = None  # ensure safe use in finally

    def setup():
        def create_random_image(file_path):
            width, height = random.randint(100, 800), random.randint(100, 800)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            image = Image.new("RGB", (width, height), color)
            image.save(file_path)

        for i in range(10):
            ext = ".jpg" if random.random() > 0.5 else ".jpeg"
            file_path = os.path.join('/tmp/', f"random_image_{i+1}{ext}")
            create_random_image(file_path)

    def test():
        target_size = (32, 32)
        folder_path = '/tmp/'
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                try:
                    with Image.open(file_path) as img:
                        if img.size != target_size:
                            print('Incorrect size:', img.size)
                            return False
                except Exception as e:
                    print(f"Failed to open {file_path}: {e}")
                    return False
        return True

    try:
        # Setup environment
        setup()

        # Extract code block if markdown-style fenced
        extracted_code = response
        if "```" in response:
            code_blocks = re.findall(r'```(?:python)?\n?(.*?)\n?```', response, re.DOTALL)
            if code_blocks:
                extracted_code = code_blocks[0]

        # Clean up quotes to prevent syntax errors
        extracted_code = extracted_code.replace('“', '"').replace('”', '"').replace('’', "'")

        # Write code to a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.py', delete=False) as temp_file:
            temp_file.write(extracted_code)
            temp_file_path = temp_file.name

        # Run the user code
        result = subprocess.run(
            ['python', temp_file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Code execution failed:\n{result.stderr.strip()}'
            }

        # Run validation
        test_result = test()
        if test_result:
            return {
                'pass': True,
                'score': 1,
                'reason': 'All images successfully resized to 32x32'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': 'Images were not properly resized to 32x32'
            }

    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Code execution timed out'
        }

    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error during execution: {str(e)}'
        }

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
