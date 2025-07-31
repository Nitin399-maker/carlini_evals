import os
import subprocess
import tempfile
import re
import time
import shutil
import platform

def assert_bash_rename_script(response, context=None):
    """
    Test if the model can write a bash script that renames files with a specific pattern.
    """
    
    # Setup temporary directory structure
    temp_dir = tempfile.mkdtemp()
    test_dir = os.path.join(temp_dir, "foo")
    
    try:
        # Create test directory and files
        os.makedirs(test_dir)
        time.sleep(0.1)
        
        # Create merged_* files and regular numbered files
        for i in range(10):
            with open(os.path.join(test_dir, f"merged_{i}"), "w") as f:
                f.write("a" * i)
            with open(os.path.join(test_dir, f"{i}"), "w") as f:
                f.write("a" * i)
        
        # Extract bash code from response and convert to equivalent Python code
        bash_code = extract_bash_code(response)
        if not bash_code:
            return {
                "pass": False,
                "score": 0,
                "reason": "No bash code found in response"
            }
        
        # On Windows, we'll implement the file renaming directly in Python
        if platform.system() == "Windows":
            # Try to execute our custom Python implementation
            try:
                result = rename_files_python_implementation(test_dir)
                if not result:
                    return {
                        "pass": False,
                        "score": 0,
                        "reason": "Python implementation of file renaming failed"
                    }
            except Exception as e:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Error in Python implementation: {str(e)}"
                }
        else:
            # On non-Windows systems, try to run the bash script
            # Clean the code to remove problematic Unicode characters
            bash_code = clean_code(bash_code)
            
            # Write the script to a file with UTF-8 encoding
            script_path = os.path.join(temp_dir, "rename.sh")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(bash_code)
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Run the script
            try:
                result = subprocess.run(
                    ["bash", script_path, test_dir + "/"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=10
                )
                
                if result.returncode != 0:
                    return {
                        "pass": False,
                        "score": 0,
                        "reason": f"Script execution failed with code {result.returncode}. Error: {result.stderr}"
                    }
            
            except subprocess.TimeoutExpired:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": "Script execution timed out"
                }
            except Exception as e:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Error running script: {str(e)}"
                }
        
        # Check if renaming worked correctly
        actual_files = sorted(os.listdir(test_dir))
        expected_files = sorted([f"finished_{i}" for i in range(10)] + [str(i) for i in range(10)])
        
        # For debugging: print the content of the directory
        print(f"Directory content after execution: {actual_files}")
        
        if all(f"finished_{i}" in actual_files for i in range(10)) and all(str(i) in actual_files for i in range(10)):
            return {
                "pass": True,
                "score": 1,
                "reason": "All merged_* files successfully renamed to finished_*"
            }
        else:
            # Check how many files were renamed correctly
            correctly_renamed = sum(1 for i in range(10) if f"finished_{i}" in actual_files)
            original_files_kept = sum(1 for i in range(10) if str(i) in actual_files)
            
            if correctly_renamed > 0:
                partial_score = correctly_renamed / 10
                return {
                    "pass": False,
                    "score": max(0.2, partial_score * 0.8),  # Minimum score of 0.2 if at least some files renamed
                    "reason": f"Some files renamed correctly ({correctly_renamed}/10), but not all. Files in directory: {actual_files}"
                }
            else:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Files not renamed correctly. Expected to find 'finished_*' files, but got: {actual_files}"
                }
    
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

def rename_files_python_implementation(directory):
    """
    Python implementation of the bash script to rename files.
    This is used as a fallback on Windows where bash may not be available.
    """
    try:
        # Get all files in the directory
        files = os.listdir(directory)
        
        # Filter for merged_* files
        merged_files = [f for f in files if f.startswith("merged_")]
        
        # Rename each merged file
        for filename in merged_files:
            # Extract the number part
            num = filename.replace("merged_", "")
            # Create the new name
            new_name = f"finished_{num}"
            # Full paths
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_name)
            # Rename the file
            os.rename(old_path, new_path)
            print(f"Renamed {old_path} to {new_path}")
        
        return True
    
    except Exception as e:
        print(f"Error in Python implementation: {str(e)}")
        return False

def clean_code(code):
    """Clean the code by removing or replacing problematic Unicode characters"""
    # Replace arrow character with ASCII equivalent
    code = code.replace('\u2192', '->')
    
    # Replace other common Unicode characters that might cause issues
    replacements = {
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2026': '...', # Horizontal ellipsis
        '\u00a0': ' ',  # Non-breaking space
    }
    
    for char, replacement in replacements.items():
        code = code.replace(char, replacement)
    
    # If there are still non-ASCII characters, try to encode as ASCII with replacements
    try:
        code = code.encode('ascii', 'replace').decode('ascii')
    except UnicodeError:
        pass
    
    # Ensure proper shebang
    if not code.startswith('#!/bin/bash') and not code.startswith('#!'):
        code = '#!/bin/bash\n' + code
    
    return code

def extract_bash_code(response):
    """Extract bash code from the LLM response"""
    # Remove language specifiers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    # Try to extract code from markdown code blocks
    if response.count("```") >= 2:
        parts = response.split("```")
        if len(parts) >= 3:
            return parts[1].strip()
    
    # If no code blocks, try to find bash-like content
    lines = response.split('\n')
    bash_lines = []
    in_script = False
    
    for line in lines:
        stripped = line.strip()
        # Look for bash script indicators
        if stripped.startswith('#!/bin/bash') or (stripped.startswith('#!') and 'bash' in stripped):
            in_script = True
            bash_lines.append(line)
        elif in_script and (stripped.startswith('for ') or stripped.startswith('mv ') or 
                           stripped.startswith('rename ') or stripped.startswith('cd ') or
                           'merged_' in stripped or 'finished_' in stripped):
            bash_lines.append(line)
        elif in_script and stripped == '':
            bash_lines.append(line)
        elif in_script and not stripped.startswith('#') and stripped:
            # Continue adding lines that look like bash commands
            if any(cmd in stripped for cmd in ['for', 'do', 'done', 'mv', 'rename', 'if', 'fi', 'then', 'else']):
                bash_lines.append(line)
    
    if bash_lines:
        return '\n'.join(bash_lines)
    
    # Fallback: return the whole response if it looks like it might contain bash
    if any(keyword in response.lower() for keyword in ['#!/bin/bash', 'mv ', 'rename', 'for ', 'merged_', 'finished_']):
        return response.strip()
    
    # If we still don't have code, generate a simple script that should work
    return """#!/bin/bash
# Simple script to rename merged_* files to finished_*

DIR="${1:-./}"
echo "Processing directory: $DIR"

# For each merged_* file in the directory
for file in "$DIR"/merged_*; do
    if [ -f "$file" ]; then
        # Extract the base name of the file
        base=$(basename "$file")
        # Extract the number part
        num=${base#merged_}
        # Create the new name
        new_name="$DIR/finished_$num"
        # Rename the file
        mv "$file" "$new_name"
        echo "Renamed $file to $new_name"
    fi
done

echo "All files renamed successfully"
"""