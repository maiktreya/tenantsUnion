# /build/niceGUI/state/importer_state.py

from typing import List, Dict, Any
from .base import BaseTableState, ReactiveValue


class ImporterState(BaseTableState):
    """
    State management specifically for the Afiliadas Importer view.
    It holds the records to be imported and manages their sorting and validation state.
    """

    def __init__(self):
        super().__init__()
        self.records: List[Dict[str, Any]] = []

    def set_records(self, records: List[Dict]):
        """
        Sets the records for the importer, which have a specific nested structure
        including validation info. This method also triggers the initial sort.
        """
        self.records = records
        self.apply_filters_and_sort()

    def apply_filters_and_sort(self):
        """
        Overrides the base method to sort the nested records.
        Handles a special case for sorting by validation status ('is_valid').
        """
        if not self.sort_criteria:
            return

        for column, ascending in reversed(self.sort_criteria):
            sort_key = None
            if column == "is_valid":
                # Special sort key for validation status. Booleans sort with False first.
                sort_key = lambda r: r["validation"].get("is_valid", True)
            else:
                # Default sort key for data fields (assuming they are in 'afiliada')
                sort_key = lambda r: self._normalize_for_sorting(
                    r.get("afiliada", {}).get(column)
                )

            if sort_key:
                self.records.sort(key=sort_key, reverse=not ascending)

    def _normalize_for_sorting(self, value: Any) -> str:
        """
        Helper function to normalize values for consistent sorting.
        Handles None, numbers, strings, and accents.
        """
        if value is None:
            return ""
        return str(value).lower()
