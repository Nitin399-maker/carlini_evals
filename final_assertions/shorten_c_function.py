import subprocess
import tempfile
import os
import re

def check_c_code_golf(response, context=None):
    """
    Check if the C code golf solution is short enough and functionally correct.
    """
    
    # Extract code from response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        else:
            return output
    
    code = extract_code(response)
    
    # Check if code is short enough (<200 bytes without whitespace)
    code_no_whitespace = code.replace(" ", "").replace("\n", "").replace("\t", "")
    if len(code_no_whitespace) >= 200:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Code too long: {len(code_no_whitespace)} bytes (must be <200)'
        }
    
    # Test case and helper functions
    test_case = '''
#include <stdio.h>

int out = 0;
int digitalWrite(int pin, int value) {
  out *= 101;
  out += pin;
  out *= 97;
  out += value;
  return out;
}

int main() {
    stepper(100);
    printf("%d", out);
    return 0;
}
'''
    
    # Prepare the code - remove main if it exists in the response
    if 'int main' in code:
        code = code.replace('int main', 'int __delete_this__main')
    
    full_code = code + "\n\n" + test_case
    
    # Create temporary files and compile/run
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(full_code)
            c_file = f.name
        
        exe_file = c_file.replace('.c', '.out')
        
        # Compile
        compile_result = subprocess.run(
            ['gcc', '-o', exe_file, c_file, '-lm'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if compile_result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Compilation failed: {compile_result.stderr}'
            }
        
        # Run
        run_result = subprocess.run(
            [exe_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if run_result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Runtime error: {run_result.stderr}'
            }
        
        # Check output
        expected_output = "-1475775710"
        actual_output = run_result.stdout.strip()
        
        if expected_output in actual_output:
            return {
                'pass': True,
                'score': 1,
                'reason': f'Success! Code length: {len(code_no_whitespace)} bytes, output correct'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Wrong output. Expected: {expected_output}, Got: {actual_output}'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Execution timed out'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error: {str(e)}'
        }
    finally:
        # Cleanup
        try:
            if 'c_file' in locals():
                os.unlink(c_file)
            if 'exe_file' in locals() and os.path.exists(exe_file):
                os.unlink(exe_file)
        except:
            pass
        
check_c_code_golf("""
Here is a 136-byte (whitespace excluded) drop-in replacement that keeps the name `stepper` and the behaviour intact.

```c
void stepper(int n){
 static const char p[]={1,3,2,6,4,12,8,9};
 for(int i=0;i<n;i++){
  char b=p[i&7];
  for(int j=0;j<4;j++)digitalWrite(j+1,(b>>j)&1);
 }
}
```

How it works  
1. The 8 coil-patterns are stored as 4-bit nibbles in the array `p`.  
2. Each iteration picks the proper pattern with `p[i&7]`.  
3. A second loop shifts through the 4 bits and writes them to pins 1-4 via `digitalWrite`.

136 bytes < 300 bytes, mission accomplished!""")        