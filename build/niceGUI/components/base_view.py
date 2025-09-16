# /build/niceGUI/views/base_view.py

from nicegui import app


class BaseView:
    """
    A base class for all views in the application.
    It provides common functionalities like role-based access control.
    """

    def has_role(self, *roles: str) -> bool:
        """
        Checks if the current user has any of the specified roles (case-insensitive).
        This method is centralized here to be inherited by all other views.
        """
        user_roles = {role.lower() for role in app.storage.user.get("roles", [])}
        required_roles = {role.lower() for role in roles}
        return not required_roles.isdisjoint(user_roles)
