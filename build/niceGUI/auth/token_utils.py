import jwt
import time
import os
import json

SECRET = os.environ.get("PGRST_JWT_SECRET")


def create_db_token(user_id: int, alias: str, roles: list[str]) -> str:
    """Mint a PostgREST-compatible JWT for a freshly-authenticated user.

    The `sub` (subject) claim carries the numeric user id; it is read by
    the self-row RLS policies on `usuarios` and `usuario_credenciales`
    (see build/postgreSQL/init-scripts/06-init-rls.sql) so an authenticated
    user can read/update only their own profile and credentials. `role`
    is the DB role PostgREST will SET ROLE into; `roles` is the custom
    array every other RLS policy reads. `alias` is kept for logs/UI.
    """
    payload = {
        "role": "web_user",  # Matches the DB role created in 06-init-rls.sql
        "sub": str(user_id),  # Subject (numeric user id; self-row RLS reads this)
        "alias": alias,  # Human-readable username, surfaced in RLS-irrelevant places
        "roles": roles,  # Custom claim consumed by every other RLS policy
        "exp": time.time() + 10800,  # Expires in 3 hours (same as the session)
        "iat": time.time(),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")