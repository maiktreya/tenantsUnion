from nicegui import app
from nicegui import ui


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
        if hasattr(self, "state") and hasattr(self.state, "clear_selection"):
            self.state.clear_selection()

        # Clear UI containers if they exist
        if hasattr(self, "data_table_container") and self.data_table_container:
            self.data_table_container.clear()

        if (
            hasattr(self, "filter_container")  # Corrected attribute check
            and self.filter_container
        ):
            self.filter_container.clear()

        if hasattr(self, "detail_container") and self.detail_container:
            self.detail_container.clear()

        # Programmatically set the value to None. This will trigger the on_change event,
        # which correctly handles clearing the view.
        if hasattr(self, "select_view") and self.select_view:
            self.select_view.set_value(None)
        if hasattr(self, "select_table") and self.select_table:
            self.select_table.set_value(None)
