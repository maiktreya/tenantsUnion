from typing import Dict, Callable, Optional


def _clean_record(record: Dict) -> Dict:
    """
    Cleans a record by converting empty strings to None and attempting
    to cast numeric strings to int or float. This helps prevent API errors
    when inserting data into typed columns.
    """
    cleaned = {}
    for key, value in record.items():
        if value is None or value == "":
            cleaned[key] = None
        else:
            try:
                # Try to convert to integer first
                cleaned[key] = int(value)
            except (ValueError, TypeError):
                try:
                    # If int conversion fails, try float
                    cleaned[key] = float(value)
                except (ValueError, TypeError):
                    # Otherwise, keep it as a string
                    cleaned[key] = value
    return cleaned
