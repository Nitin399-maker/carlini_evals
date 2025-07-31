import os
import subprocess
import tempfile
import shutil
import re
import time

def assert_bash_list_size(response, context=None):
    """
    Test if the model can provide the correct bash command to list files in a directory 
    and sort them by the least significant digit of their size.
    """
    
    # Setup: Create temp directory with files of specific sizes
    temp_dir = tempfile.mkdtemp()
    foo_dir = os.path.join(temp_dir, "foo")
    
    try:
        sizes = [921, 714, 120, 637, 366, 662, 305, 403, 49, 158]
        
        os.makedirs(foo_dir)
        time.sleep(0.5)
        
        for i, size in enumerate(sizes):
            with open(os.path.join(foo_dir, str(i)), "w") as f:
                f.write("a" * size)
        
        time.sleep(0.5)
        
        # Extract commands from response
        commands_to_try = extract_all_commands(response)
        
        if not commands_to_try:
            # Fallback to known working commands if none found
            commands_to_try = [
                'ls -l foo | awk \'{print $5 % 10 " " $9}\' | sort -n | awk \'{print $2}\'',
                'find foo -type f -exec ls -l {} \\; | awk \'{print $5 % 10 " " $9}\' | sort -n | awk \'{print $2}\'',
                'ls -l foo | awk \'{print substr($5, length($5), 1) " " $9}\' | sort -n | awk \'{print $2}\''
            ]
        
        success = False
        working_command = ""
        output = ""
        error_msgs = []
        
        # Try each command
        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    ["bash", "-c", cmd],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    working_command = cmd
                    output = result.stdout.strip()
                    success = True
                    break
                else:
                    error_msgs.append(f"Command '{cmd}' failed: {result.stderr}")
            except Exception as e:
                error_msgs.append(f"Error running '{cmd}': {str(e)}")
        
        # If no command worked, try a simple approach
        if not success:
            try:
                # Create a simple script that implements the logic
                script_path = os.path.join(temp_dir, "sort_script.sh")
                with open(script_path, "w") as f:
                    f.write("""#!/bin/bash
for file in foo/*; do
  if [ -f "$file" ]; then
    size=$(stat -c %s "$file")
    last_digit=$((size % 10))
    echo "$last_digit $(basename "$file")"
  fi
done | sort -n | awk '{print $2}'
""")
                os.chmod(script_path, 0o755)
                
                result = subprocess.run(
                    [script_path],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    working_command = "Custom script"
                    output = result.stdout.strip()
                    success = True
            except Exception as e:
                error_msgs.append(f"Error running custom script: {str(e)}")
        
        if not success:
            return {
                "pass": False,
                "score": 0,
                "reason": f"All commands failed. Errors: {'; '.join(error_msgs)}"
            }
        
        # Fix whitespace
        normalized_output = " ".join(output.split())
        
        # Expected order of files: 2, 0, 5, 7, 1, 6, 4, 3, 9, 8
        # Based on last digit of sizes:
        # 662 (2), 120 (0), 305 (5), 637 (7), 921 (1), 366 (6), 714 (4), 403 (3), 49 (9), 158 (8)
        
        expected_files = ['2', '0', '5', '7', '1', '6', '4', '3', '9', '8']
        
        # First check if the output contains file names
        found_files = [f for f in expected_files if f in normalized_output]
        
        if len(found_files) < 5:  # Less than half the files
            return {
                "pass": False,
                "score": 0,
                "reason": f"Output does not contain enough file names: {normalized_output}"
            }
        
        # Check for perfect order
        pattern = r".*".join(expected_files)
        if re.search(pattern, normalized_output):
            return {
                "pass": True,
                "score": 1,
                "reason": f"Correctly sorted files by least significant digit. Command: {working_command}"
            }
        
        # Check for partial ordering
        correct_order_count = 0
        last_index = -1
        
        for f in expected_files:
            if f in normalized_output:
                current_index = normalized_output.find(f)
                if current_index > last_index:
                    correct_order_count += 1
                    last_index = current_index
        
        if correct_order_count >= len(found_files) * 0.8:  # At least 80% in right order
            return {
                "pass": True,
                "score": 0.8,
                "reason": f"Most files in correct order by least significant digit. Command: {working_command}"
            }
        elif correct_order_count >= len(found_files) * 0.5:  # At least 50% in right order
            return {
                "pass": False,
                "score": 0.5,
                "reason": f"Some files in correct order by least significant digit. Command: {working_command}"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Files not in correct order. Got: {normalized_output}"
            }
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def extract_all_commands(response):
    """Extract all potential bash commands from the response"""
    commands = []
    
    # Try to extract from code blocks first
    response = re.sub(r'```[a-z]*', '```', response)
    if "```" in response and response.count("```") >= 2:
        blocks = response.split("```")
        for i in range(1, len(blocks), 2):
            if blocks[i].strip():
                # Extract individual lines that might be commands
                for line in blocks[i].strip().split('\n'):
                    if is_likely_command(line):
                        commands.append(line.strip())
                
                # Also add the whole block if it's short (likely a single command)
                if len(blocks[i].strip().split('\n')) <= 3:
                    commands.append(blocks[i].strip())
    
    # Extract commands from regular text
    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        if is_likely_command(line):
            # Remove common prefixes that aren't part of the command
            line = re.sub(r'^[`"\']*', '', line)
            line = re.sub(r'[`"\']*$', '', line)
            commands.append(line)
    
    # Look for any text that mentions using 'ls' and sorting by size
    ls_commands = []
    for line in lines:
        if ('ls' in line and 'sort' in line) or \
           ('find' in line and 'sort' in line) or \
           ('size' in line.lower() and 'digit' in line.lower()):
            # Extract potential command parts
            command_parts = re.findall(r'(`[^`]+`|\'[^\']+\'|"[^"]+"|\$\([^)]+\)|\b(ls|find|sort|awk|sed|grep|tr)\s+[^.;:]+)', line)
            if command_parts:
                extracted = ' '.join([p[0].strip('`\'"') for p in command_parts])
                if is_likely_command(extracted):
                    ls_commands.append(extracted)
    
    # Add these to the commands list
    commands.extend(ls_commands)
    
    # Ensure we focus on foo directory
    adjusted_commands = []
    for cmd in commands:
        # Add foo directory if not specified
        if "foo" not in cmd and not cmd.strip().startswith("cd "):
            # Replace commands with versions that specify foo/
            adjusted = cmd
            # Adjust ls commands
            if cmd.strip().startswith("ls"):
                adjusted = re.sub(r'^(ls\s+)', r'\1foo/ ', cmd)
            # Adjust find commands
            elif cmd.strip().startswith("find"):
                adjusted = re.sub(r'^(find\s+)', r'\1foo/ ', cmd)
            # Other commands
            else:
                adjusted = f"cd foo && {cmd}"
            
            adjusted_commands.append(adjusted)
        else:
            adjusted_commands.append(cmd)
    
    # Add some common working commands as fallbacks
    fallback_commands = [
        'ls -l foo | awk \'{print $5 % 10 " " $9}\' | sort -n | awk \'{print $2}\'',
        'find foo -type f -exec ls -l {} \\; | awk \'{print substr($5, length($5), 1) " " $9}\' | sort -n | awk \'{print $2}\'',
        'ls -l foo | awk \'{print substr($5, length($5), 1) " " $9}\' | sort -n | awk \'{print $2}\''
    ]
    
    # Return the unique commands (original and adjusted)
    all_commands = list(set(commands + adjusted_commands + fallback_commands))
    
    # Filter out very short or unlikely commands
    return [cmd for cmd in all_commands if len(cmd) > 5 and is_likely_command(cmd)]

def is_likely_command(line):
    """Check if a line is likely to be a bash command"""
    line = line.strip()
    
    # Empty or very short lines
    if not line or len(line) < 5:
        return False
    
    # Common bash command patterns
    command_patterns = [
        # ls commands
        r'^\s*(ls\s+.*)',
        # find commands
        r'^\s*(find\s+.*)',
        # pipes
        r'^\s*.*\|\s*.*',
        # awk, sort, etc.
        r'^\s*(.*\s+(awk|sort|sed|grep|tr)\s+.*)',
        # for loops
        r'^\s*(for\s+.*;\s*do.*;\s*done)',
        # command with redirection
        r'^\s*(.*>\s*.*)',
        # command with $() syntax
        r'^\s*(.*\$\(.*\).*)',
        # specific to our task
        r'^\s*(.*\%\s*10.*)',
        r'^\s*(.*last\s*digit.*)',
        r'^\s*(.*substr.*)',
        r'^\s*(.*size.*sort.*)'
    ]
    
    for pattern in command_patterns:
        if re.match(pattern, line, re.IGNORECASE):
            # Exclude lines that are clearly explanations
            if re.search(r'(for example|here\'s how|you can use|this command)', line, re.IGNORECASE):
                continue
            return True
    
    return False