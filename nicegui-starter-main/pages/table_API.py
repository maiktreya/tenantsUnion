import theme
from nicegui import ui


def title_generator():
    with theme.frame("YouTube Title Generator"):

        # Sample data: list of dicts
        users = [
            {"name": "Alice", "age": 30, "role": "Engineer"},
            {"name": "Bob", "age": 25, "role": "Designer"},
            {"name": "Carol", "age": 29, "role": "Manager"},
        ]

        # Define columns for the table
        columns = [
            {"name": "name", "label": "Name", "field": "name"},
            {"name": "age", "label": "Age", "field": "age"},
            {"name": "role", "label": "Role", "field": "role"},
        ]

        # Create a table UI with tooltip on 'role' column header
        table = ui.table(
            columns=columns,
            rows=users,
            row_key="name",
        )
        # Add tooltip to the 'Role' header
        role_header = table._props["columns"][2]  # Get the 'role' column
        role_header["headerTooltip"] = "The user's job function in the company"
