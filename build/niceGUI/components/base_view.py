from nicegui import app
from nicegui import ui  # Make sure ui is imported

class BaseView:
    """
    A base class for all views in the application.
    It provides common functionalities like role-based access control and UI helpers.
    """

    def has_role(self, *roles: str) -> bool:
        """
        Checks if the current user has any of the specified roles (case-insensitive).
        """
        user_roles = {role.lower() for role in app.storage.user.get("roles", [])}
        required_roles = {role.lower() for role in roles}
        return not required_roles.isdisjoint(user_roles)

    def clear_view_internals(self):
        """
        A reusable method to clear common UI containers and state.
        It safely checks if the attributes exist on the instance before acting.
        """
        # Clear the state object's data
        if hasattr(self, 'state') and hasattr(self.state, 'clear_selection'):
            self.state.clear_selection()

        # Clear UI containers if they exist
        if hasattr(self, 'data_table_container') and self.data_table_container:
            self.data_table_container.clear()
        
        if hasattr(self, 'state') and hasattr(self.state, 'filter_container') and self.state.filter_container:
            self.state.filter_container.clear()

        if hasattr(self, 'detail_container') and self.detail_container:
            self.detail_container.clear()
            
        # Also clear the select component's value
        if hasattr(self, 'select_view') and self.select_view:
            self.select_view.value = None
        if hasattr(self, 'select_table') and self.select_table:
            self.select_table.value = None

