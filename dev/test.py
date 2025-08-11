#!/usr/bin/env python3
from datetime import datetime
from nicegui import ui

# --- Data Structures ---
# In a real-world application, this data would come from a database.
# For this template, we use a simple dictionary to represent the company-headquarters relationship.
COMPANIES = {
    'Innovate Corp': ['New York HQ', 'London Innovation Hub', 'Tokyo R&D Center'],
    'Quantum Solutions': ['Berlin Main Office', 'Silicon Valley Labs'],
    'Synergy Enterprises': ['Global HQ (Singapore)', 'European Operations (Paris)'],
    'Apex Dynamics': ['Chicago Office'],
}

# This list will act as our in-memory "database" to store the note records.
# Each record is a dictionary.
records = []

# --- UI Layout and Logic ---

@ui.page('/')
def main_page():
    """Defines the layout and functionality of the main application page."""

    # A function to handle saving the note.
    def save_note():
        """
        Validates input, creates a record, adds it to our data store,
        and provides user feedback.
        """
        # Ensure all fields are filled before saving
        if not company_select.value or not hq_select.value or not note_content.value:
            ui.notify('Please fill all fields before saving.', type='warning')
            return

        # Create the new record
        new_record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'company': company_select.value,
            'headquarters': hq_select.value,
            'note': note_content.value,
        }

        # Add to our records list and update the table
        records.append(new_record)

        # Provide user feedback
        ui.notify(f"Note for {hq_select.value} saved successfully!", type='positive')

        # Clear the text area for the next note
        note_content.value = ''

        # Refresh the table to show the new entry
        records_table.update()


    # A function to update the headquarters dropdown when a company is selected.
    def update_headquarters_options():
        """
        Clears and repopulates the headquarters select based on the chosen company.
        """
        selected_company = company_select.value
        # When a new company is selected, clear the old headquarters selection
        hq_select.value = None
        # Update the available options for the headquarters select.
        # The `set_options` method only takes the list of options as an argument.
        hq_select.set_options(COMPANIES.get(selected_company, []))
        hq_select.update()


    # --- UI Elements ---

    # App Header
    ui.add_head_html('<style>.nicegui-content { padding: 1rem; }</style>')
    with ui.header(elevated=True).classes('bg-primary text-white items-center'):
        ui.label('Corporate Minutes & Notes').classes('text-2xl font-bold')

    # Main container for a clean layout
    with ui.card().classes('w-full max-w-4xl mx-auto mt-8'):
        ui.label('Step 1: Select Company and Headquarters').classes('text-xl font-semibold')

        # Selection row
        with ui.row().classes('w-full items-center'):
            # Company Selector
            company_select = ui.select(
                list(COMPANIES.keys()),
                label='Company',
                on_change=update_headquarters_options
            ).classes('w-64')

            # Headquarters Selector (initially empty)
            # The `clearable` property is set here, at creation time.
            hq_select = ui.select(
                [],
                label='Headquarters',
                clearable=True
            ).classes('w-64')

    # Note-taking section - This card will only appear when a headquarters is selected.
    with ui.card().classes('w-full max-w-4xl mx-auto mt-4').bind_visibility_from(hq_select, 'value', bool):
        ui.label('Step 2: Write and Save Your Note').classes('text-xl font-semibold')

        # Large text area for notes
        note_content = ui.textarea(placeholder='Write your meeting minutes or notes here...') \
            .props('outlined rounded').classes('w-full')

        # Save button
        ui.button('Save Note', on_click=save_note, icon='save').classes('mt-2')

    # Records display section
    with ui.card().classes('w-full max-w-4xl mx-auto mt-4'):
        ui.label('Saved Records').classes('text-xl font-semibold')

        # Define the columns for our records table
        columns = [
            {'name': 'timestamp', 'label': 'Timestamp', 'field': 'timestamp', 'required': True, 'align': 'left', 'sortable': True},
            {'name': 'company', 'label': 'Company', 'field': 'company', 'align': 'left', 'sortable': True},
            {'name': 'headquarters', 'label': 'Headquarters', 'field': 'headquarters', 'align': 'left', 'sortable': True},
            {'name': 'note', 'label': 'Note', 'field': 'note', 'align': 'left', 'style': 'white-space: pre-wrap;'},
        ]

        # The table that displays the records
        records_table = ui.table(columns=columns, rows=records, row_key='timestamp').classes('w-full')


# --- Run the Application ---
ui.run()
