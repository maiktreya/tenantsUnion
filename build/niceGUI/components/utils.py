from typing import Dict, Callable, Optional
from datetime import datetime


def format_date_es(date_str: Optional[str]) -> Optional[str]:
    """Formats an ISO-like date string (YYYY-MM-DD...) to Spanish format (DD/MM/YYYY)."""
    if not date_str:
        return None
    try:
        # Assuming the date starts in a standard format like YYYY-MM-DD
        dt = datetime.fromisoformat(date_str.split("T")[0])
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return date_str  # Return original if parsing fails


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
