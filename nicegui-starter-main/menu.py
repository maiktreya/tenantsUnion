from nicegui import ui


def menu() -> None:
    ui.link("Home", "/").classes(replace="text-black")
    ui.link("Test API", "/api-generator/").classes(replace="text-black")
