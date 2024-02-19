from datetime import datetime, timedelta

def is_valid_date_format(date_str: str) -> bool:
    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False
    return True

def is_valid_date_range(date_str: str, data) -> bool:
    today = datetime.now().date()
    max_date = today + timedelta(days=7)
    input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    return today <= input_date <= max_date and date_str in data["dates"]
