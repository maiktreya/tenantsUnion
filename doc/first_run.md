# Local Development Environment Setup (dev_run)

This guide explains how to run the application on your local machine for development and testing. This setup uses artificial data to protect privacy and exposes the application directly, without the production Nginx reverse proxy.

## 1. Environment Setup

Before running the application, configure your `.env` file for a development environment. This ensures you're using the correct database scripts and port settings.

Open your `.env` file and make sure the following variables are set:

- For development data (artificial, from a single SQL file):
  `INIT_SCRIPTS_PATH=./build/postgreSQL/init-scripts-dev`

- For direct access on `http://localhost:8081`:

- `INIT_SCRIPTS_PATH`: This points to the directory containing the `artificial_data.sql` script, which will populate the database with safe, fictional data.

- `DEV_MODE`: If set to true makes niceGUI bind mount "rw". If left blank the default for the folder is a more secure "ro".

## 2. Exposing ports externally

You have to force upserting `docker-compose-dev.yaml` over `docker-compose.yaml` to get ports **5432(postgreSQL)**, **3000(postgREST)** and **8081(niceGUI)** externally exposed (bear in mind nginx, in production, provides additional security layers).

## 3. Initial Credential Setup (CRITICAL SECURITY STEP)

### Generate Hashed Credentials Locally

Before starting the application for the first time, you **MUST** generate secure password hashes for development users. Never use plaintext credentials in documentation or repository files.

#### Step 1: Create a Python script to generate password hashes

Create a temporary file named `generate_dev_credentials.py` in your project root:

```python
#!/usr/bin/env python3
"""
Generate secure bcrypt password hashes for development users.
Run this script locally to create credentials for the artificial_data.sql initialization.
"""

from passlib.context import CryptContext
import json
from pathlib import Path

# Use the same context as the application
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_credentials():
    """
    Generate test user credentials with hashed passwords.
    
    IMPORTANT:
    - Do NOT commit plaintext passwords to the repository.
    - Do NOT share generated hashes publicly (they can still be targeted).
    - Change these credentials for production environments.
    - Use strong, unique passwords for actual deployments.
    """
    
    # Define test users with temporary development passwords
    test_users = {
        "admin_user": {
            "alias": "admin_dev",
            "nombre": "Administrador",
            "apellidos": "Desarrollo",
            "email": "admin@development.local",
            "temp_password": "AdminDev2025!Secure"  # Change this
        },
        "gestor_user": {
            "alias": "gestor_dev",
            "nombre": "Gestor",
            "apellidos": "Desarrollo",
            "email": "gestor@development.local",
            "temp_password": "GestorDev2025!Secure"  # Change this
        },
        "actas_user": {
            "alias": "actas_dev",
            "nombre": "Actas",
            "apellidos": "Desarrollo",
            "email": "actas@development.local",
            "temp_password": "ActasDev2025!Secure"  # Change this
        }
    }
    
    # Generate hashes
    credentials = {}
    for user_key, user_data in test_users.items():
        hashed_password = pwd_context.hash(user_data["temp_password"])
        credentials[user_key] = {
            "alias": user_data["alias"],
            "nombre": user_data["nombre"],
            "apellidos": user_data["apellidos"],
            "email": user_data["email"],
            "password_hash": hashed_password
        }
        print(f"\n✅ User '{user_data['alias']}':")
        print(f"   Username: {user_data['alias']}")
        print(f"   Temporary password: {user_data['temp_password']}")
        print(f"   Bcrypt hash: {hashed_password}")
        print(f"   ⚠️  SAVE the password above - you'll need it to log in for the FIRST TIME ONLY")
    
    # Optionally save hashes to a file (FOR LOCAL USE ONLY)
    output_file = Path("dev_credentials.json")
    with open(output_file, "w") as f:
        json.dump(credentials, f, indent=2)
    
    print(f"\n📄 Credentials saved to: {output_file}")
    print("⚠️  CRITICAL: Never commit this file to git or share publicly!")
    print("⚠️  Add 'dev_credentials.json' to your .gitignore immediately!")
    
    return credentials

if __name__ == "__main__":
    print("🔐 TenantsUnion Development Credential Generator")
    print("=" * 60)
    print("⚠️  This script generates test credentials for LOCAL development only.")
    print("=" * 60)
    
    try:
        credentials = generate_credentials()
        
        print("\n" + "=" * 60)
        print("✅ NEXT STEPS:")
        print("=" * 60)
        print("1. Copy the password hashes above into your artificial_data.sql file")
        print("2. Update the INSERT INTO usuarios statement with the generated hashes")
        print("3. Delete this script and dev_credentials.json after setup")
        print("4. Start the application with: docker compose --profile Frontend up -d")
        print("5. On first login, change your password via 'Mi Perfil' (My Profile)")
        print("=" * 60 + "\n")
        
    except ImportError:
        print("❌ ERROR: passlib not installed!")
        print("Install it with: pip install passlib")
        exit(1)
```

#### Step 2: Run the script

```bash
# Install required dependency (if not already installed)
pip install passlib

# Run the credential generator
python generate_dev_credentials.py
```

This will output:
```
✅ User 'admin_dev':
   Username: admin_dev
   Temporary password: AdminDev2025!Secure
   Bcrypt hash: $2b$12$...
```

#### Step 3: Update artificial_data.sql

Locate `build/postgreSQL/init-scripts-dev/artificial_data.sql` and update the user insertion section with the generated hashes:

```sql
-- INSERT sample users with HASHED passwords
-- Passwords are bcrypt hashed using passlib.CryptContext
INSERT INTO usuarios (alias, nombre, apellidos, email, password_hash, created_at, updated_at) VALUES
  ('admin_dev', 'Administrador', 'Desarrollo', 'admin@development.local', '$2b$12$YOUR_GENERATED_ADMIN_HASH_HERE', now(), now()),
  ('gestor_dev', 'Gestor', 'Desarrollo', 'gestor@development.local', '$2b$12$YOUR_GENERATED_GESTOR_HASH_HERE', now(), now()),
  ('actas_dev', 'Actas', 'Desarrollo', 'actas@development.local', '$2b$12$YOUR_GENERATED_ACTAS_HASH_HERE', now(), now());
```

#### Step 4: Clean up

```bash
# Remove the generator script and credentials file
rm generate_dev_credentials.py dev_credentials.json

# Ensure .gitignore includes these patterns
echo "dev_credentials.json" >> .gitignore
echo "generate_dev_credentials.py" >> .gitignore
```

## 4. Running the Application

With the `.env` file configured and credentials set up, you can start the application using the Frontend profile. This profile includes the database, the API, and the NiceGUI application, but excludes the Nginx and Certbot services.

Execute the following command from the root of the project:

```bash
 # for the standard fully dockerized dev environment
 docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d

 # if you have a local python environment with the requirements installed you could run the frontend directly from source
 docker compose -f docker-compose.yaml -f docker-compose-dev.yaml up -d && python build/niceGUI/main.py

 # for allowing an environment with a local postgreSQL instance with hot reload and monitor logs
 docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d --renew-anon-volumes && docker logs --follow tenantsunion-db-1
```

This command will:

- Build the necessary Docker images if they don't exist.

- Start the **db**, **server**, and **nicegui-app** services in the background (-d). exposing DB/Frontend ports.

- The db service will automatically run the script specified by `INIT_SCRIPTS_PATH`, creating the schema and populating it with artificial data.

## 5. Accessing the Application layers

Once the containers are running, you can access the application directly in your web browser at:

```bash
http://localhost:8081
```

### First-Time Login

1. Use one of the generated usernames (e.g., `admin_dev`, `gestor_dev`, or `actas_dev`)
2. Use the temporary password displayed when you ran `generate_dev_credentials.py`
3. After successful login, immediately change your password via **Mi Perfil** (My Profile)

The api would be available on your local network at (example endpoint to table afiliadas):

```bash
http://localhost:3000/afiliadas
```

And also locally available, you would be able to access the postgreSQL instance at:

```bash
postgresql://app_user:password@localhost:5432/mydb?search_path=sindicato_inq
```

## 6. Available Roles and Permissions

Three role-based access levels are available for testing:

- **admin**: Full access to all tables and functions, user management, system administration.
- **gestor**: Access to conflicts management, afiliadas importer, and read-only views module.
- **actas**: Access limited to the conflicts module only.

Each role has Row-Level Security (RLS) policies enforced at the database level to ensure data segregation.

## 7. Session Management and Security

- **Session Duration**: Authenticated sessions expire after **3 hours** (server-side enforcement).
- **Rate Limiting**: Login attempts are limited to 10 per minute per IP. After 5 failures, an account is locked for 15 minutes.
- **Password Hashing**: All passwords are hashed using bcrypt (14-round salt by default).
- **JWT Tokens**: Authentication uses JWT tokens with 3-hour expiration time.

## 8. Forcing stop and cleaning

From your project's root run the following to stop & remove all the containers and images afterwards:

```bash
docker compose --profile Frontend down -v && docker system prune -a --volumes -f
```

---

## 🔒 Security Best Practices for Development

- ✅ Always generate credentials locally using the provided script
- ✅ Never commit hashed passwords or plaintext credentials to the repository
- ✅ Update temporary passwords immediately after first login
- ✅ Use `.gitignore` to exclude credential files
- ✅ Rotate credentials regularly for production deployments
- ✅ Use strong, unique passwords (minimum 12 characters with mixed case, numbers, and symbols)
- ❌ Never share generated hashes or passwords publicly
- ❌ Don't use development credentials in production
