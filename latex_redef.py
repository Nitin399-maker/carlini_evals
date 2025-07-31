def check_latex_redef(response, context=None):
    """
    Test if a model can use latex \\renewcommand, and do a bit more than what I actually asked.
    
    Evaluates: ((SubstringEvaluator("\\renewcommand{\\paragraph}") | SubstringEvaluator("\\renewcommand\\paragraph")) 
                & SubstringEvaluator("\\bigskip") & SubstringEvaluator("\\textbf") & SubstringEvaluator("\\noindent"))
    """
    
    # Check for renewcommand (either format)
    has_renewcommand_braces = "\\renewcommand{\\paragraph}" in response
    has_renewcommand_no_braces = "\\renewcommand\\paragraph" in response
    has_renewcommand = has_renewcommand_braces or has_renewcommand_no_braces
    
    # Check for required substrings
    has_bigskip = "\\bigskip" in response
    has_textbf = "\\textbf" in response
    has_noindent = "\\noindent" in response
    
    # Final evaluation: renewcommand AND bigskip AND textbf AND noindent
    passes = has_renewcommand and has_bigskip and has_textbf and has_noindent
    
    return {
        "pass": passes,
        "score": 1.0 if passes else 0.0,
        "reason": f"renewcommand: {has_renewcommand}, bigskip: {has_bigskip}, textbf: {has_textbf}, noindent: {has_noindent}"
    }