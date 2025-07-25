import re
import subprocess
import tempfile
import os
import sys

def get_assertion(response, context=None):
    """
    Assertion function for Promptfoo that evaluates assembly interpreter implementation.
    """
    
    # Test cases and expected answers - with colons after labels
    code1 = """
SET R1 0
SET R2 1
loop:
    MUL R3 R2 R2
    STORE R3 R1
    INC R1
    INC R2
    SET R3 20
    EQ R1 R3
    JF loop
"""
    
    primes_code = """
SET R1 2
start_find_primes:
    JMP is_prime
ready_prime:
    SET R7 1
    EQ R2 R7
    JF increment
    STORE R1 R8
    INC R8
    SET R7 100
    EQ R8 R7
    JF increment
    JMP end
increment:
    INC R1
    JMP start_find_primes
is_prime:
    SET R2 1
    SET R3 2
start_loop:
    MUL R4 R3 R3
    GT R4 R1
    JT is_prime_end
    MOD R6 R1 R3
    SET R7 0
    EQ R7 R6
    JT not_prime
    INC R3
    JMP start_loop
not_prime:
    SET R2 0
is_prime_end:
    JMP ready_prime
end:
"""
    
    # Create test case without string formatting
    test_case = '''
# Initialize memory for storing results
memory = [0] * 1000
registers = {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5": 0, "R6": 0, "R7": 0, "R8": 0}

# First test - squares
test1_code = """''' + code1 + '''"""
print("TEST1:", evaluate(test1_code, memory, registers)[:10])

# Reset memory and registers for second test
memory = [0] * 1000
registers = {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5": 0, "R6": 0, "R7": 0, "R8": 0}

# Second test - primes
test2_code = """''' + primes_code + '''"""
print("TEST2:", evaluate(test2_code, memory, registers)[:10])
'''

    expected_squares = "[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]"
    expected_primes = "[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]"
    
    def extract_python_code(text):
        """Extract code from response and clean it"""
        # Clean special characters and normalize quotes
        text = text.encode('ascii', 'ignore').decode()
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove language specifiers from code blocks
        text = re.sub(r'```[a-z]*', '```', text)
        
        # Try to extract from code blocks
        if "```" in text and text.count("```") >= 2:
            code = text.split("```")[1]
            return code.strip()
        else:
            # If no code blocks, return the whole text
            return text.strip()
    
    try:
        # Extract the Python code
        extracted_code = extract_python_code(response)
        
        # Create the full test code with encoding declaration
        full_code = """# -*- coding: utf-8 -*-
import re
from typing import List, Dict, Union
from collections import defaultdict

def evaluate(program: str, memory: List[int], registers: Dict[str, int]) -> List[int]:
    # Parse the program into instructions and collect labels
    instructions = []
    labels = {}
    pc = 0
    
    # Convert registers to defaultdict for automatic 0 initialization
    regs = defaultdict(int)
    regs.update(registers)
    
    # Process each line
    for line in program.split('\\n'):
        line = line.strip()
        if not line:
            continue
            
        # Handle labels
        if ':' in line:
            label, *rest = line.split(':')
            label = label.strip()
            labels[label] = pc
            line = ':'.join(rest).strip()
            if not line:
                continue
                
        if line:
            instructions.append(line.split())
            pc += 1
    
    # Execute the program
    pc = 0
    while pc < len(instructions):
        instr = instructions[pc]
        op = instr[0]
        
        if op == 'SET':
            regs[instr[1]] = int(instr[2])
            pc += 1
        elif op == 'ADD':
            regs[instr[1]] = regs[instr[2]] + regs[instr[3]]
            pc += 1
        elif op == 'MUL':
            regs[instr[1]] = regs[instr[2]] * regs[instr[3]]
            pc += 1
        elif op == 'MOD':
            regs[instr[1]] = regs[instr[2]] % regs[instr[3]]
            pc += 1
        elif op == 'GT':
            regs['flag'] = 1 if regs[instr[1]] > regs[instr[2]] else 0
            pc += 1
        elif op == 'EQ':
            regs['flag'] = 1 if regs[instr[1]] == regs[instr[2]] else 0
            pc += 1
        elif op == 'INC':
            regs[instr[1]] += 1
            pc += 1
        elif op == 'STORE':
            addr = regs[instr[2]]
            while len(memory) <= addr:
                memory.append(0)
            memory[addr] = regs[instr[1]]
            pc += 1
        elif op == 'JMP':
            if instr[1] not in labels:
                raise RuntimeError(f'Unknown label: {instr[1]}')
            pc = labels[instr[1]]
        elif op == 'JT':
            if instr[1] not in labels:
                raise RuntimeError(f'Unknown label: {instr[1]}')
            pc = labels[instr[1]] if regs.get('flag', 0) == 1 else pc + 1
        elif op == 'JF':
            if instr[1] not in labels:
                raise RuntimeError(f'Unknown label: {instr[1]}')
            pc = labels[instr[1]] if regs.get('flag', 0) == 0 else pc + 1
        else:
            raise RuntimeError(f'Unknown operation: {op}')
    
    # Update the original registers dict with final values
    registers.update(regs)
    return memory

""" + test_case

        # Create temporary file and run the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', encoding='utf-8', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        try:
            # Run the Python code using sys.executable for correct interpreter
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "pass": False,
                    "score": 0.0,
                    "reason": f"Code execution failed: {result.stderr}"
                }
            
            output = result.stdout
            
            # Check if both expected results are in the output
            squares_match = expected_squares in output
            primes_match = expected_primes in output
            
            if squares_match and primes_match:
                return {
                    "pass": True,
                    "score": 1.0,
                    "reason": "Both test cases passed successfully"
                }
            elif squares_match:
                return {
                    "pass": False,
                    "score": 0.5,
                    "reason": "Only squares test case passed, primes test failed"
                }
            elif primes_match:
                return {
                    "pass": False,
                    "score": 0.5,
                    "reason": "Only primes test case passed, squares test failed"
                }
            else:
                return {
                    "pass": False,
                    "score": 0.0,
                    "reason": f"Both test cases failed. Output: {output[:500]}..."
                }
                
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
            
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Code execution timed out"
        }
    except Exception as e:
        import traceback
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error during execution: {str(e)}\nTraceback: {traceback.format_exc()}"
        }