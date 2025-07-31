import subprocess
import tempfile
import os
import re

def assert_sql_table_creation(response, context=None):
    """
    Test if the model can generate a SQL query to create a database table.
    Extracts SQL from response, runs it, and checks for specific content.
    """
    
    # Extract SQL code from response (similar to ExtractCode)
    sql_code = extract_sql_code(response)
    if not sql_code:
        return {
            "pass": False,
            "score": 0,
            "reason": "No SQL code found in response"
        }
    
    # Run SQL code (similar to SQLRun)
    try:
        result = run_sql_code(sql_code)
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"SQL execution failed: {str(e)}"
        }
    
    # Evaluate result (similar to PyEvaluator with myfn)
    success = evaluate_sql_result(result)
    
    return {
        "pass": success,
        "score": 1 if success else 0,
        "reason": f"SQL result evaluation: {'passed' if success else 'failed'} - found Nicholas, age 5, researcher" if success else "Missing required data in SQL result"
    }

def extract_sql_code(response):
    """Extract SQL code from response, handling code blocks"""
    # Remove language specifiers from code blocks
    cleaned_response = re.sub(r'```[a-z]*', '```', response)
    
    # Try to extract from code blocks first
    if "```" in cleaned_response and cleaned_response.count("```") >= 2:
        parts = cleaned_response.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    
    # If no clear code blocks, return the whole response
    return response.strip()

def run_sql_code(sql_code):
    """Run SQL code using sqlite3 subprocess"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql_code)
        sql_file = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_file = f.name
    
    try:
        # Run sqlite3 with the SQL file
        cmd = ['sqlite3', '-init', sql_file, db_file, '.exit']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Now query the database to check contents
        query_cmd = ['sqlite3', db_file, 'SELECT * FROM people;']
        query_result = subprocess.run(query_cmd, capture_output=True, text=True, timeout=30)
        
        return query_result.stdout
        
    finally:
        # Clean up temp files
        try:
            os.unlink(sql_file)
            os.unlink(db_file)
        except:
            pass

def evaluate_sql_result(result):
    """Evaluate if the SQL result contains expected data"""
    if not result:
        return False
    
    result_lower = result.lower()
    
    # Check for Nicholas, age 5, and researcher/research
    has_nicholas = "nicholas" in result_lower
    has_age_5 = "5" in result
    has_research = "research" in result_lower
    
    return has_nicholas and has_age_5 and has_research