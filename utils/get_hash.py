import getpass

try:
    from passlib.context import CryptContext
except ImportError:
    print("❌ Error: 'passlib' is not installed.")
    print("Please install it by running: pip install 'passlib[bcrypt]'")
    exit(1)

def create_user_credentials():
    """
    Interactively creates a user credential hash and generates the corresponding SQL statement.
    """
    print("--- Sindicato User Credential Generator ---")

    user_alias = input("Enter the user's alias (from the 'usuarios' table): ")
    if not user_alias:
        print("Username cannot be empty.")
        return

    try:
        user_id = int(input(f"Enter the numeric ID for '{user_alias}' (from the 'usuarios.id' column): "))
    except ValueError:
        print("Invalid ID. Please enter a number.")
        return

    password = getpass.getpass("Enter the new password (input will be hidden): ")
    password_confirm = getpass.getpass("Confirm the new password: ")

    if password != password_confirm:
        print("❌ Passwords do not match. Please try again.")
        return

    if not password:
        print("Password cannot be empty.")
        return

    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(password)
    except Exception as e:
        print(f"An error occurred while hashing the password: {e}")
        return

    sql_command = (
    f"UPDATE sindicato_inq.usuario_credenciales SET password_hash = '{hashed_password}' "
    f"WHERE usuario_id = {user_id};"
    )

    print("\n✅ Success! Your SQL command is ready.")
    print("--------------------------------------------------")
    print("Copy and run the following command in your PostgreSQL database:")
    print("\n" + sql_command + "\n")
    print("--------------------------------------------------")

if __name__ == "__main__":
    create_user_credentials()