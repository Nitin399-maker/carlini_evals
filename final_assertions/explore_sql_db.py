import sqlite3
import subprocess
import os
import tempfile
import re
import json
import requests

def assert_sql_interaction(response, context=None):
    """
    Test if the model can interact with an SQLite database and provide the correct 
    command to add a new person with specific criteria.
    """
    
    def setup_database():
        """Create and populate the test database."""
        db_path = os.path.join(tempfile.gettempdir(), 'people.db')
        
        # Remove existing database if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''CREATE TABLE people
                     (a_name TEXT, favorite_friend TEXT, person_age INT, the_profession TEXT)''')
        
        # Insert test data
        people_data = [
            ('Alice', 'Bob', 29, 'Engineer'),
            ('Bob', 'Alice', 32, 'Doctor'),
            ('Charlie', 'Alice', 28, 'Artist'),
            ('David', 'Eve', 35, 'Doctor'),
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
        
        return db_path
    
    def extract_sql_command(text):
        """Extract SQL command from response."""
        # Clean up the text
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)
        
        # Try various patterns to extract SQL command
        patterns = [
            # Match complete INSERT statement
            r'INSERT\s+INTO\s+people\s*\([^)]*\)\s*VALUES\s*\([^)]*\)\s*;',
            # Match any INSERT statement
            r'INSERT\s+INTO\s+people[^;]*;',
            # Match between quotes
            r'[\'"`]([^\'"`]*INSERT[^\'"`]*)[\'"`]',
            # Match after INPUT: or similar
            r'(?:INPUT:|COMMAND:|SQL:)\s*([^;]*;)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the first match and clean it
                command = matches[0]
                # Remove any surrounding quotes
                command = command.strip('\'"`')
                # Ensure it ends with semicolon
                if not command.strip().endswith(';'):
                    command += ';'
                return command
        
        # If no pattern matched, try to find anything that looks like an INSERT
        if 'INSERT' in text.upper():
            # Extract from INSERT to the next semicolon or end of string
            match = re.search(r'INSERT[^;]*;?', text, re.IGNORECASE)
            if match:
                command = match.group(0)
                if not command.endswith(';'):
                    command += ';'
                return command
        
        return None
    
    def execute_sql(db_path, command):
        """Execute SQL command and return result."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Print debug info
            print(f"Executing SQL command: {command}")
            
            cursor.execute(command)
            conn.commit()
            
            # Verify the insertion
            cursor.execute("SELECT * FROM people WHERE a_name = 'Victor'")
            result = cursor.fetchone()
            print(f"Verification query result: {result}")
            
            conn.close()
            return True
            
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return False
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return False
    
    def get_required_values(db_path):
        """Get the youngest age and most common profession."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get youngest age
        cursor.execute('SELECT MIN(person_age) FROM people')
        youngest_age = cursor.fetchone()[0]
        print(f"Youngest age found: {youngest_age}")
        
        # Get most common profession
        cursor.execute('''
            SELECT the_profession, COUNT(*) as count 
            FROM people 
            GROUP BY the_profession 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        most_common_profession = result[0] if result else None
        print(f"Most common profession found: {most_common_profession}")
        
        conn.close()
        return youngest_age, most_common_profession
    
    def verify_victor(db_path):
        """Verify Victor was added with correct criteria."""
        try:
            youngest_age, most_common_profession = get_required_values(db_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check Victor's details
            cursor.execute('''
                SELECT person_age, the_profession 
                FROM people 
                WHERE a_name = 'Victor'
            ''')
            result = cursor.fetchone()
            print(f"Victor's details: {result}")
            
            conn.close()
            
            if not result:
                return False, "Victor not found in database"
            
            age, profession = result
            if age != youngest_age:
                return False, f"Wrong age: got {age}, expected {youngest_age}"
            if profession != most_common_profession:
                return False, f"Wrong profession: got {profession}, expected {most_common_profession}"
                
            return True, "Victor added correctly"
            
        except Exception as e:
            return False, f"Verification error: {str(e)}"
    
    try:
        # Setup database
        db_path = setup_database()
        print(f"Database created at: {db_path}")
        
        # Extract SQL command
        command = extract_sql_command(response)
        if not command:
            return {
                'pass': False,
                'score': 0.0,
                'reason': 'No valid SQL command found in response'
            }
        
        print(f"Extracted SQL command: {command}")
        
        # Fix common issues in the command
        command = command.replace('"', "'")  # Standardize quotes
        command = re.sub(r'\s+', ' ', command)  # Fix whitespace
        command = command.strip()
        if not command.endswith(';'):
            command += ';'
        
        print(f"Processed SQL command: {command}")
        
        # Execute the command
        if not execute_sql(db_path, command):
            return {
                'pass': False,
                'score': 0.0,
                'reason': 'SQL command execution failed'
            }
        
        # Verify the result
        success, message = verify_victor(db_path)
        
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
        
        return {
            'pass': success,
            'score': 1.0 if success else 0.0,
            'reason': message
        }
        
    except Exception as e:
        if 'db_path' in locals() and os.path.exists(db_path):
            os.remove(db_path)
        return {
            'pass': False,
            'score': 0.0,
            'reason': f'Error during evaluation: {str(e)}'
        }