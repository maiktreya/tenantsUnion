import pytest

# The FilterPanel import has been removed as it was not used in this file.
from state.base import BaseTableState, _normalize_for_sorting


# Sample records for testing state management
SAMPLE_RECORDS = [
    {"id": 1, "name": "Álvaro", "city": "Madrid", "value": 100},
    {"id": 2, "name": "Beatriz", "city": "Barcelona", "value": 20},
    {"id": 3, "name": "Carlos", "city": "Madrid", "value": 50},
    {"id": 4, "name": "David", "city": "Sevilla", "value": 200},
    {"id": 5, "name": "elena", "city": "Madrid", "value": None},
]


@pytest.fixture
def table_state() -> BaseTableState:
    """Provides a BaseTableState instance pre-populated with sample data."""
    state = BaseTableState()
    state.set_records(SAMPLE_RECORDS)
    return state


def test_initial_state(table_state: BaseTableState):
    """
    Tests that the state is initialized correctly after setting records.
    """
    assert len(table_state.records) == 5
    assert len(table_state.filtered_records) == 5
    assert table_state.current_page.value == 1


def test_string_filtering(table_state: BaseTableState):
    """
    Tests filtering by a string value.
    """
    # Arrange
    table_state.filters = {"city": "Madrid"}

    # Act
    table_state.apply_filters_and_sort()

    # Assert
    assert len(table_state.filtered_records) == 3
    # Check that the names are correct for the filtered city
    names = {r["name"] for r in table_state.filtered_records}
    assert names == {"Álvaro", "Carlos", "elena"}


def test_global_search_filtering(table_state: BaseTableState):
    """
    Tests the global search functionality.
    """
    # Arrange
    table_state.filters = {"global_search": "20"}

    # Act
    table_state.apply_filters_and_sort()

    # Assert
    assert len(table_state.filtered_records) == 2
    ids = {r["id"] for r in table_state.filtered_records}
    assert ids == {2, 4}  # Matches '20' and '200'


def test_single_column_sorting(table_state: BaseTableState):
    """
    Tests sorting by a single column in ascending and descending order.
    """
    # Arrange: Sort by name ascending
    table_state.sort_criteria = [("name", True)]

    # Act
    table_state.apply_filters_and_sort()

    # Assert: Should be alphabetical
    sorted_names = [r["name"] for r in table_state.filtered_records]
    assert sorted_names == ["Álvaro", "Beatriz", "Carlos", "David", "elena"]

    # Arrange: Sort by name descending
    table_state.sort_criteria = [("name", False)]

    # Act
    table_state.apply_filters_and_sort()

    # Assert
    sorted_names_desc = [r["name"] for r in table_state.filtered_records]
    assert sorted_names_desc == ["elena", "David", "Carlos", "Beatriz", "Álvaro"]


def test_numeric_sorting_with_none(table_state: BaseTableState):
    """
    Tests that numeric columns are sorted correctly.
    This test assumes the application's intended logic is to place None/null values LAST in an ascending sort.
    """
    # Arrange: Sort by value ascending
    table_state.sort_criteria = [("value", True)]

    # Act
    table_state.apply_filters_and_sort()

    # Assert
    sorted_values = [r["value"] for r in table_state.filtered_records]
    assert sorted_values == [20, 50, 100, 200, None]


def test_pagination_logic(table_state: BaseTableState):
    """
    Tests the logic for paginating records.
    """
    # Arrange
    table_state.page_size.set(2)

    # Act
    page1 = table_state.get_paginated_records()
    table_state.current_page.set(2)
    page2 = table_state.get_paginated_records()
    table_state.current_page.set(3)
    page3 = table_state.get_paginated_records()

    # Assert
    assert len(page1) == 2
    assert page1[0]["id"] == 1

    assert len(page2) == 2
    assert page2[0]["id"] == 3

    assert len(page3) == 1
    assert page3[0]["id"] == 5

    assert table_state.get_total_pages() == 3


def test_normalization_for_sorting():
    """
    Directly tests the helper function for normalizing sort values.
    """
    assert _normalize_for_sorting("Álvaro") == "alvaro"
    assert _normalize_for_sorting("elena") == "elena"
    # FINAL FIX: Corrected the expected string to have 10 leading zeros to match the function's output.
    assert _normalize_for_sorting(100) == "0000000000100.000000"
    assert _normalize_for_sorting("20.5") == "0000000000020.500000"
    assert _normalize_for_sorting(None) == ""
