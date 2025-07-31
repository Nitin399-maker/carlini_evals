def assert_date_news_headlines(response, context=None):
    """
    Test if the model can predict the date a few news headlines were published.
    Expects the response to contain "2020-04-05".
    """
    expected_date = "2020-04-05"
    
    if expected_date in response:
        return {
            "pass": True,
            "score": 1.0,
            "reason": f"Found expected date '{expected_date}' in response"
        }
    else:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Expected date '{expected_date}' not found in response"
        }