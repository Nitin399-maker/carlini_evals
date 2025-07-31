def check_email_extraction(response, context=None):
    """
    Evaluates if the model correctly extracted all invalid email addresses
    while avoiding false positives like hostnames and IP addresses.
    """
    
    # Required email addresses that should be present
    required_emails = [
        "foo-bar@example.com",
        "noperson628@gmail.com", 
        "againredacted@example.info",
        "xsz032by05wfk5jpe@mail4you.biz",
        "wontsay@bestpay.com.cn",
        "redactedfinally@gmail.com"
    ]
    
    # Strings that should NOT be present (hostnames/IPs, not emails)
    forbidden_strings = [
        "gmail-smtp-in.l.google.com",
        "217.69.139.180"
    ]
    
    # Check all required emails are present
    missing_emails = []
    for email in required_emails:
        if email not in response:
            missing_emails.append(email)
    
    # Check forbidden strings are not present
    found_forbidden = []
    for forbidden in forbidden_strings:
        if forbidden in response:
            found_forbidden.append(forbidden)
    
    # Determine pass/fail
    passed = len(missing_emails) == 0 and len(found_forbidden) == 0
    
    # Build score and reason
    score = 1.0 if passed else 0.0
    
    reason_parts = []
    if missing_emails:
        reason_parts.append(f"Missing emails: {', '.join(missing_emails)}")
    if found_forbidden:
        reason_parts.append(f"Contains forbidden strings: {', '.join(found_forbidden)}")
    
    if passed:
        reason = "All invalid emails extracted correctly, no false positives"
    else:
        reason = "; ".join(reason_parts)
    
    return {
        "pass": passed,
        "score": score,
        "reason": reason
    }