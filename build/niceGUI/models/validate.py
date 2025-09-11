# /build/niceGUI/models/validate.py

from typing import Dict, Any, List, Tuple
from config import TABLE_INFO
import re
from datetime import datetime


class TableValidator:
    """Config-driven validation using TABLE_INFO metadata."""

    def __init__(self):
        self.table_info = TABLE_INFO

    def validate_record(
        self, table: str, data: Dict[str, Any], operation: str = "create"
    ) -> Tuple[bool, List[str]]:
        """
        Validate a record against table configuration.

        Args:
            table: Table name
            data: Record data to validate
            operation: 'create', 'update', or 'read'
        """
        if table not in self.table_info:
            return False, [f"Unknown table: {table}"]

        config = self.table_info[table]
        errors = []

        # Validate field options (enums)
        field_options = config.get("field_options", {})
        for field, options in field_options.items():
            if field in data and data[field] is not None and data[field] != "":
                if data[field] not in options:
                    errors.append(
                        f"Invalid {field}: '{data[field]}'. Must be one of: {options}"
                    )

        # Validate required fields (for create operations)
        if operation == "create":
            required_fields = config.get("required_fields", [])
            for field in required_fields:
                value = data.get(field)
                if value is None or value == "":
                    errors.append(f"Missing required field: {field}")

        # Validate field types based on common patterns
        errors.extend(self._validate_field_types(table, data))

        # Validate relationships exist (optional, can be expanded)
        errors.extend(self._validate_relationships(table, data))

        return len(errors) == 0, errors

    def _validate_field_types(self, table: str, data: Dict[str, Any]) -> List[str]:
        """Validate field types based on naming conventions."""
        errors = []
        for field, value in data.items():
            # --- ENHANCEMENT ---
            # Skip validation for any field that is None or an empty string.
            # This allows optional fields (like dates) to be truly empty.
            if value is None or value == "":
                continue

            # Email validation
            if "email" in field.lower():
                if not re.match(r"^[^@]+@[^@]+\.[^@]+$", str(value)):
                    errors.append(f"Invalid email format for '{field}'")

            # Date validation
            if any(date_word in field.lower() for date_word in ["fecha", "date"]):
                if not self._is_valid_date(value):
                    errors.append(
                        f"Invalid date format for '{field}' (expected YYYY-MM-DD)"
                    )

            # ID field validation
            if field.endswith("_id"):
                try:
                    int(value)
                except (ValueError, TypeError):
                    errors.append(f"Invalid ID format for '{field}' (must be a number)")

        return errors

    def _validate_relationships(self, table: str, data: Dict[str, Any]) -> List[str]:
        """Placeholder for validating foreign key relationships."""
        errors = []
        # This section can be expanded in the future to perform database lookups
        # to confirm that a foreign key (e.g., 'piso_id') actually exists.
        # For now, basic type validation is handled in _validate_field_types.
        return errors

    def _is_valid_date(self, value: Any) -> bool:
        """Check if a value is a valid ISO 8601 date string (YYYY-MM-DD)."""
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            try:
                # Use strptime for stricter format checking (YYYY-MM-DD)
                datetime.strptime(value, "%Y-%m-%d")
                return True
            except ValueError:
                # Fallback for full ISO format with time, etc.
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                    return True
                except ValueError:
                    return False
        return False

    def get_field_constraints(self, table: str, field: str) -> Dict[str, Any]:
        """Get validation constraints for a specific field from TABLE_INFO."""
        if table not in self.table_info:
            return {}

        config = self.table_info[table]
        constraints = {}

        # Field options (enums)
        field_options = config.get("field_options", {})
        if field in field_options:
            constraints["options"] = field_options[field]

        # Required fields
        required_fields = config.get("required_fields", [])
        constraints["required"] = field in required_fields

        # Relationships
        relations = config.get("relations", {})
        if field in relations:
            constraints["relationship"] = relations[field]

        return constraints


# Create a singleton instance for easy import across the application
validator = TableValidator()
