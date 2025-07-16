from nicegui import ui
from pages.table_API import api_generator


def create() -> None:

    ui.page("/api-generator/")(api_generator)


if __name__ == "__main__":
    create()
