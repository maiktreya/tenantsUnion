# tests/test_filters.py

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Add the project root to the Python path to allow imports from the app source
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build.niceGUI.components.filters import FilterPanel


# Sample data for testing, includes multiple date columns
@pytest.fixture
def sample_records():
    return [
        {
            "id": 1,
            "name": "Event A",
            "status": "active",
            "fecha_alta": "2025-01-15T10:00:00Z",
            "fecha_baja": None,
        },
        {
            "id": 2,
            "name": "Event B",
            "status": "inactive",
            "fecha_alta": "2025-02-20T11:00:00Z",
            "fecha_baja": "2025-08-01T11:00:00Z",
        },
        {
            "id": 3,
            "name": "Event C",
            "status": "active",
            "fecha_alta": "2025-03-25T12:00:00Z",
            "fecha_baja": None,
        },
    ]


# Pytest fixture to create a fresh FilterPanel instance for each test
@pytest.fixture
def filter_panel_with_mock_callback(sample_records):
    """
    Creates an instance of FilterPanel and mocks the on_filter_change callback
    to track its calls and arguments.
    """
    # MagicMock will act as our fake callback function
    mock_callback = MagicMock()

    panel = FilterPanel(records=sample_records, on_filter_change=mock_callback)
    # We need to call refresh() to populate the component's internal structures
    # In the real app, this happens after create()
    panel.refresh()

    # Yield both the panel and the mock so tests can use them
    yield panel, mock_callback


def test_filter_panel_initialization(filter_panel_with_mock_callback):
    """
    Tests if the FilterPanel correctly identifies standard and date columns
    upon initialization.
    """
    panel, _ = filter_panel_with_mock_callback

    # The refresh method should have identified the columns
    assert "global_search" in panel.inputs
    assert "status" in panel.inputs

    # Check if it correctly found the date columns for the single date filter UI
    assert panel.date_field_select is not None
    assert "fecha_alta" in panel.date_field_select.options
    assert "fecha_baja" in panel.date_field_select.options


def test_on_date_change_emits_correct_event(filter_panel_with_mock_callback):
    """
    Tests if selecting a date range triggers the callback with the correct
    key and value structure.
    """
    panel, mock_callback = filter_panel_with_mock_callback

    # 1. Simulate the user selecting 'fecha_alta' from the dropdown
    panel._on_date_field_select(MagicMock(value="fecha_alta"))

    # 2. Simulate the user picking a start date
    panel._on_date_change(part="start", value="2025-01-01")

    # Assert that the callback was called
    mock_callback.assert_called()

    # Assert that it was called with the correct arguments
    expected_key = "date_range_fecha_alta"
    expected_value = {"start": "2025-01-01", "end": None}
    mock_callback.assert_called_with(expected_key, expected_value)

    # 3. Simulate the user picking an end date
    panel._on_date_change(part="end", value="2025-03-31")

    expected_value_updated = {"start": "2025-01-01", "end": "2025-03-31"}
    mock_callback.assert_called_with(expected_key, expected_value_updated)


def test_selecting_new_date_field_clears_old_filter(filter_panel_with_mock_callback):
    """
    Tests the critical logic that ensures the old date filter is cleared from
    the application state when the user selects a new date field.
    """
    panel, mock_callback = filter_panel_with_mock_callback

    # 1. User selects the first date field and sets a value
    panel._on_date_field_select(MagicMock(value="fecha_alta"))
    panel._on_date_change(part="start", value="2025-01-01")

    # Verify the initial filter was set
    mock_callback.assert_called_with(
        "date_range_fecha_alta", {"start": "2025-01-01", "end": None}
    )

    # 2. Now, user selects a DIFFERENT date field from the dropdown
    panel._on_date_field_select(MagicMock(value="fecha_baja"))

    # Assert that the callback was called again, this time with a `None` value
    # for the OLD key, effectively clearing that filter in the parent state.
    mock_callback.assert_called_with("date_range_fecha_alta", None)

    # The currently selected column should now be 'fecha_baja'
    assert panel.selected_date_column == "fecha_baja"


def test_clearing_date_field_selection(filter_panel_with_mock_callback):
    """
    Tests that clearing the selection in the date field dropdown also
    clears the filter.
    """
    panel, mock_callback = filter_panel_with_mock_callback

    # 1. User selects a date field and sets a value
    panel._on_date_field_select(MagicMock(value="fecha_alta"))
    panel._on_date_change(part="start", value="2025-01-01")
    mock_callback.assert_called_with(
        "date_range_fecha_alta", {"start": "2025-01-01", "end": None}
    )

    # 2. User clicks the 'x' to clear the dropdown selection
    panel._on_date_field_select(MagicMock(value=None))

    # Assert the callback was called to clear the 'fecha_alta' filter
    mock_callback.assert_called_with("date_range_fecha_alta", None)
    assert panel.selected_date_column is None
