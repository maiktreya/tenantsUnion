# tests/test_home_view.py

from nicegui import ui
from nicegui.testing import Screen
from build.niceGUI.views.home import HomeView


def test_home_view_creation(screen: Screen):
    """
    Tests that the HomeView is created without errors.
    """
    # Arrange & Act
    with screen.app, ui.row() as container:
        home_view = HomeView(navigate=lambda: None)
        home_view.create()

    # Assert
    screen.should_contain("Bienvenido al Sistema de Gestión")
    screen.should_contain("Mi Perfil")
