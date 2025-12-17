import jwt
import time
import os
import json

SECRET = os.environ.get("PGRST_JWT_SECRET", "default-secret")


def create_db_token(username: str, roles: list[str]) -> str:
    payload = {
        "role": "web_user",  # Matches the DB role we created in Step 2
        "sub": username,  # Subject (user identifier)
        "roles": roles,  # Custom claim for our RLS policies
        "exp": time.time() + 10800,  # Expires in 3 hours (same as your session)
        "iat": time.time(),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")
