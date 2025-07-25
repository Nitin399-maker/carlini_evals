import subprocess
import tempfile
import os
import re
import sqlite3
import time

def assert_sql_query_response(response, context=None):
    """
    Evaluates if the model's response contains a correct Python program 
    that retrieves data from a SQL database and outputs 'Grace'.
    """
    
    # Setup the database first
    setup_database()
    
    # Extract and clean Python code from the response
    code = extract_python_code(response)
    if not code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'No Python code found in response'
        }
    
    # Clean the code and ensure proper encoding
    code = clean_code(code)
    
    # Run the extracted code
    try:
        output = run_python_code(code)
        
        # Check if output contains "Grace"
        if "Grace" in output:
            return {
                'pass': True,
                'score': 1,
                'reason': 'Code successfully outputs Grace'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Code output does not contain "Grace". Output: {output}'
            }
            
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error running code: {str(e)}'
        }
    finally:
        # Clean up database file
        cleanup_database()

def setup_database():
    """Create the SQLite database with test data"""
    conn = sqlite3.connect('people.db')
    cursor = conn.cursor()
    
    # Drop table if exists
    cursor.execute('DROP TABLE IF EXISTS people')
    
    # Create table
    cursor.execute('''CREATE TABLE people
                 (name TEXT, favorite_friend TEXT, age INT, profession TEXT)''')
    
    # Insert test data
    people_data = [
        ('Alice', 'Bob', 29, 'Engineer'),
        ('Bob', 'Alice', 32, 'Doctor'),
        ('Charlie', 'Alice', 28, 'Artist'),
        ('David', 'Eve', 35, 'Architect'),
        ('Eve', 'Frank', 26, 'Teacher'),
        ('Frank', 'Alice', 31, 'Scientist'),
        ('Grace', 'Heidi', 30, 'Nurse'),
        ('Heidi', 'Ivy', 25, 'Lawyer'),
        ('Ivy', 'Charlie', 34, 'Chef'),
        ('Judy', 'Grace', 27, 'Accountant')
    ]
    
    cursor.executemany('INSERT INTO people VALUES (?,?,?,?)', people_data)
    conn.commit()
    conn.close()

def extract_python_code(response):
    """Extract Python code from the model's response"""
    # Remove language specifiers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    if "```" in response:
        # Extract code between triple backticks
        parts = response.split("```")
        if len(parts) >= 2:
            return parts[1]
    
    # If no code blocks found, return the entire response
    return response

def clean_code(code):
    """Clean the code and ensure proper encoding"""
    # Replace common problematic characters
    replacements = {
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201c': '"',  # Left double quote
        '\u201d': '"',  # Right double quote
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2026': '...', # Ellipsis
        '\xa0': ' ',    # Non-breaking space
    }
    
    # Apply replacements
    for old, new in replacements.items():
        code = code.replace(old, new)
    
    # Convert to ASCII, replacing any remaining non-ASCII characters
    code = code.encode('ascii', 'replace').decode('ascii')
    
    # Ensure proper imports are present
    if 'import sqlite3' not in code:
        code = 'import sqlite3\n' + code
    
    # Add encoding declaration at the top
    if not code.startswith('# -*- coding:'):
        code = '# -*- coding: utf-8 -*-\n' + code
    
    return code

def run_python_code(code):
    """Run Python code and return its output"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Code execution failed: {result.stderr}")
            
        return result.stdout
        
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def cleanup_database():
    """Remove the test database file with retry (for Windows file lock issues)"""
    db_path = 'people.db'
    retries = 5
    delay = 0.5  # seconds

    for attempt in range(retries):
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            return
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise