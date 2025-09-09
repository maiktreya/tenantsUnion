# validation.py (new file)
from typing import Dict, Any, List, Tuple, Optional
from config import TABLE_INFO
import re
from datetime import datetime

class TableValidator:
    """Config-driven validation using TABLE_INFO metadata."""

    def __init__(self):
        self.table_info = TABLE_INFO

    def validate_record(self, table: str, data: Dict[str, Any],
                       operation: str = "create") -> Tuple[bool, List[str]]:
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
            if field in data and data[field] is not None:
                if data[field] not in options:
                    errors.append(f"Invalid {field}: '{data[field]}'. Must be one of: {options}")

        # Validate required fields (for create operations)
        if operation == "create":
            required_fields = config.get("required_fields", [])
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Missing required field: {field}")

        # Validate field types based on common patterns
        errors.extend(self._validate_field_types(table, data))

        # Validate relationships exist
        errors.extend(self._validate_relationships(table, data))

        return len(errors) == 0, errors

    def _validate_field_types(self, table: str, data: Dict[str, Any]) -> List[str]:
        """Validate field types based on naming conventions."""
        errors = []

        for field, value in data.items():
            if value is None:
                continue

            # Email validation
            if 'email' in field.lower() and value:
                if not re.match(r'^[^@]+@[^@]+\.[^@]+$', str(value)):
                    errors.append(f"Invalid email format: {field}")

            # Date validation
            if any(date_word in field.lower() for date_word in ['fecha', 'date']):
                if not self._is_valid_date(value):
                    errors.append(f"Invalid date format: {field}")

            # ID field validation
            if field.endswith('_id') and value:
                try:
                    int(value)
                except (ValueError, TypeError):
                    errors.append(f"Invalid ID format: {field}")

        return errors

    def _validate_relationships(self, table: str, data: Dict[str, Any]) -> List[str]:
        """Validate foreign key relationships."""
        errors = []
        config = self.table_info[table]
        relations = config.get("relations", {})

        for field, relation_info in relations.items():
            if field in data and data[field] is not None:
                # Here you could add actual FK validation by querying the related table
                # For now, just validate the field exists and has a reasonable value
                if not data[field]:
                    errors.append(f"Invalid relationship value for {field}")

        return errors

    def _is_valid_date(self, value: Any) -> bool:
        """Check if value is a valid date."""
        if isinstance(value, datetime):
            return True

        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return True
            except ValueError:
                pass

        return False

    def get_field_constraints(self, table: str, field: str) -> Dict[str, Any]:
        """Get validation constraints for a specific field."""
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

# Create singleton instance
validator = TableValidator()