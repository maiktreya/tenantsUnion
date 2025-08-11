from nicegui import ui

# Example user data
users = [
    {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "role": "Admin"},
    {"id": 2, "name": "Bob Johnson", "email": "bob@example.com", "role": "User"},
    {"id": 3, "name": "Carol Lee", "email": "carol@example.com", "role": "User"},
]
next_id = 4  # Track next user ID


def refresh_table():
    user_table.rows = [(u["id"], u["name"], u["email"], u["role"], "") for u in users]


def add_user(name, email, role):
    global next_id
    users.append(
        {
            "id": next_id,
            "name": name,
            "email": email,
            "role": role,
        }
    )
    next_id += 1
    refresh_table()


def delete_user(user_id):
    global users
    users[:] = [u for u in users if u["id"] != user_id]
    refresh_table()


with ui.card().style("max-width: 600px; margin: 2rem auto;"):
    ui.label("User Administration").classes("text-h5 text-center")

    # --- Add User Form ---
    with ui.form("Add New User"):
        name = ui.input("Name").props("outlined")
        email = ui.input("Email").props("outlined")
        role = ui.select(["Admin", "User"], "Role").props("outlined")

        @ui.button("Add User", color="primary")
        async def on_add():
            if name.value and email.value and role.value:
                add_user(name.value, email.value, role.value)
                name.value = ""
                email.value = ""
                role.value = None

    ui.separator()

    # --- User Table ---
    user_table = ui.table(
        columns=[
            {
                "name": "id",
                "label": "ID",
                "field": "id",
                "required": True,
                "sortable": True,
                "align": "left",
            },
            {"name": "name", "label": "Name", "field": "name", "sortable": True},
            {"name": "email", "label": "Email", "field": "email", "sortable": True},
            {"name": "role", "label": "Role", "field": "role", "sortable": True},
            {"name": "actions", "label": "Actions", "field": "actions"},
        ],
        rows=[(u["id"], u["name"], u["email"], u["role"], "") for u in users],
        row_key="id",
    ).classes("w-full")

    # --- Add Delete Buttons ---
    @user_table.add_slot("body-cell-actions")
    def actions_slot(row):
        ui.button(
            icon="delete",
            color="negative",
            on_click=lambda: delete_user(row["id"]),
            size="sm",
        )


# Start app
refresh_table()
ui.run(title="User Admin Demo")
