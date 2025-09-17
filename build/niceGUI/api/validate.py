# /build/niceGUI/api/validate.py

from typing import Dict, Any, List, Tuple
import re
from datetime import datetime
from config import TABLE_INFO


class TableValidator:
    """Config-driven validation using TABLE_INFO metadata."""

    def __init__(self):
        self.table_info = TABLE_INFO

    def validate_record(
        self, table: str, data: Dict[str, Any], operation: str = "create"
    ) -> Tuple[bool, List[str]]:
        """
        Validate a record against table configuration using a prioritized set of rules.
        """
        if table not in self.table_info:
            return False, [f"Unknown table: {table}"]

        config = self.table_info[table]
        errors = []

        # Rule 1: Validate required fields (for 'create' operations)
        if operation == "create":
            required_fields = config.get("required_fields", [])
            for field in required_fields:
                value = data.get(field)
                if value is None or str(value).strip() == "":
                    errors.append(f"Falta el campo obligatorio: {field}")

        # Rule 2: Validate field options (enums)
        field_options = config.get("field_options", {})
        for field, options in field_options.items():
            value = data.get(field)
            if value is not None and str(value).strip() != "":
                if value not in options:
                    errors.append(
                        f"Valor inválido para {field}: '{value}'. Debe ser uno de: {options}"
                    )

        # Rule 3: Validate field patterns (regex for formats like IBAN, email, etc.)
        field_patterns = config.get("field_patterns", {})
        for field, pattern_info in field_patterns.items():
            value = data.get(field)
            if value is not None and str(value).strip() != "":
                regex = pattern_info.get("regex")
                if regex and not re.match(regex, str(value)):
                    error_message = pattern_info.get(
                        "error_message", f"Formato inválido para el campo '{field}'"
                    )
                    errors.append(error_message)

        # Rule 4: Validate field types based on naming conventions (fallback)
        errors.extend(self._validate_field_types(table, data))

        # Rule 5: Validate relationships (placeholder for future expansion)
        errors.extend(self._validate_relationships(table, data))

        return len(errors) == 0, errors

    def _validate_field_types(self, table: str, data: Dict[str, Any]) -> List[str]:
        """Validate field types based on naming conventions."""
        errors = []
        # --- THIS IS THE FIX ---
        # Get the config for the current table to correctly check for existing patterns.
        config = self.table_info.get(table, {})
        # ---------------------

        for field, value in data.items():
            if value is None or str(value).strip() == "":
                continue

            # Email validation (can be replaced by a pattern in config.py)
            if "email" in field.lower():
                # Avoid re-validating if a pattern already exists for this field
                if not config.get("field_patterns", {}).get(field):
                    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", str(value)):
                        errors.append(f"Formato de email inválido para '{field}'")

            # Date validation
            if any(date_word in field.lower() for date_word in ["fecha", "date"]):
                if not self._is_valid_date(value):
                    errors.append(
                        f"Formato de fecha inválido para '{field}' (se esperaba AAAA-MM-DD)"
                    )

            # ID field validation
            if field.endswith("_id"):
                try:
                    int(value)
                except (ValueError, TypeError):
                    errors.append(f"El formato del ID para '{field}' debe ser numérico")

        return errors

    def _validate_relationships(self, table: str, data: Dict[str, Any]) -> List[str]:
        """Placeholder for validating foreign key relationships."""
        return []

    def _is_valid_date(self, value: Any) -> bool:
        """Check if a value is a valid ISO 8601 date string (YYYY-MM-DD)."""
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            try:
                datetime.strptime(value, "%Y-%m-%d")
                return True
            except ValueError:
                try:
                    # Fallback for full ISO format with time, etc.
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
        if field in config.get("field_options", {}):
            constraints["options"] = config["field_options"][field]

        # Required fields
        constraints["required"] = field in config.get("required_fields", [])

        # Pattern validation
        if field in config.get("field_patterns", {}):
            constraints["pattern"] = config["field_patterns"][field]

        # Relationships
        if field in config.get("relations", {}):
            constraints["relationship"] = config["relations"][field]

        return constraints


# Create a singleton instance for easy import across the application
validator = TableValidator()
