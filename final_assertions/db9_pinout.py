def test_db9_port_knowledge(response, context=None):
    """Test if a model knows about old computer ports when prompted ambiguously."""
    
    # Check if any of the valid DB-9 port identifiers are present in the response
    valid_identifiers = ["DB-9", "DB9", "DE-9", "DE9"]
    
    for identifier in valid_identifiers:
        if identifier in response:
            return {
                "pass": True,
                "score": 1.0,
                "reason": f"Found valid DB-9 port identifier: {identifier}"
            }
    
    return {
        "pass": False,
        "score": 0.0,
        "reason": f"No valid DB-9 port identifiers found. Expected one of: {', '.join(valid_identifiers)}"
    }