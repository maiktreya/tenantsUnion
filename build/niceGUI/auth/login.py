# build/niceGUI/auth/login.py

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi.responses import RedirectResponse
from nicegui import app, ui
from passlib.context import CryptContext

from api.client import APIClient
from auth.token_utils import create_db_token

log = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple in-memory brute-force guard.
# Stores {username: {"failures": int, "locked_until": datetime | None}}
# This resets on process restart, which is acceptable for a single-process
# deployment. For multi-process / multi-container setups, move this to Redis
# or a DB table.
_login_attempts: dict = {}
_MAX_FAILURES = 5
_LOCKOUT_MINUTES = 15


# =====================================================================
# HELPERS
# =====================================================================

def _is_locked(username: str) -> bool:
    entry = _login_attempts.get(username)
    if not entry:
        return False
    locked_until = entry.get("locked_until")
    if locked_until and datetime.now(timezone.utc) < locked_until:
        return True
    # Lock expired — clean up so the counter resets
    if locked_until and datetime.now(timezone.utc) >= locked_until:
        _login_attempts.pop(username, None)
    return False


def _record_failure(username: str) -> None:
    entry = _login_attempts.setdefault(username, {"failures": 0, "locked_until": None})
    entry["failures"] += 1
    if entry["failures"] >= _MAX_FAILURES:
        entry["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=_LOCKOUT_MINUTES)
        log.warning(
            "Login account locked after %d failures: %s (until %s)",
            _MAX_FAILURES,
            username,
            entry["locked_until"].isoformat(),
        )


def _clear_failures(username: str) -> None:
    _login_attempts.pop(username, None)


async def _get_user_roles(api_client: APIClient, user_id: int) -> List[str]:
    """Fetch role names for a given user ID."""
    try:
        links = await api_client.get_records(
            "usuario_roles", {"usuario_id": f"eq.{user_id}"}
        )
        if not links:
            return []
        role_ids = [lnk["role_id"] for lnk in links]
        roles = await api_client.get_records(
            "roles", {"id": f'in.({",".join(map(str, role_ids))})'}
        )
        return [r.get("nombre", "") for r in roles if r.get("nombre")]
    except Exception:
        log.exception("Error fetching roles for user_id=%s", user_id)
        return []


# =====================================================================
# PAGE FACTORY
# =====================================================================

def create_login_page(api_client: APIClient):
    """Register the /login page with NiceGUI."""

    @ui.page("/login")
    async def login_page(redirect_to: str = "/") -> Optional[RedirectResponse]:

        # Already authenticated — skip straight to destination
        if app.storage.user.get("authenticated", False):
            return RedirectResponse(redirect_to)

        # ----------------------------------------------------------------
        # Core login handler
        # ----------------------------------------------------------------
        async def try_login() -> None:
            raw_user = (username.value or "").strip()
            raw_pass = password.value or ""

            if not raw_user or not raw_pass:
                ui.notify("Username and password are required.", type="negative")
                return

            # Brute-force guard
            if _is_locked(raw_user):
                remaining = (
                    _login_attempts[raw_user]["locked_until"] - datetime.now(timezone.utc)
                )
                mins = int(remaining.total_seconds() // 60) + 1
                ui.notify(
                    f"Too many failed attempts. Try again in {mins} minute(s).",
                    type="negative",
                )
                log.warning("Blocked login attempt for locked account: %s", raw_user)
                return

            # Look up user
            try:
                user_records = await api_client.get_records(
                    "usuarios", {"alias": f"eq.{raw_user}"}
                )
            except Exception:
                log.exception("DB error looking up user: %s", raw_user)
                ui.notify("A server error occurred. Please try again.", type="negative")
                return

            if not user_records:
                _record_failure(raw_user)
                ui.notify("Wrong username or password.", type="negative")
                return

            user = user_records[0]
            user_id: int = user["id"]

            # Fetch credentials
            try:
                cred_records = await api_client.get_records(
                    "usuario_credenciales", {"usuario_id": f"eq.{user_id}"}
                )
            except Exception:
                log.exception("DB error fetching credentials for user_id=%s", user_id)
                ui.notify("A server error occurred. Please try again.", type="negative")
                return

            if not cred_records:
                # User exists but has no password set — treat as auth failure
                log.warning("No credentials found for user_id=%s", user_id)
                _record_failure(raw_user)
                ui.notify("Wrong username or password.", type="negative")
                return

            stored_hash: str = cred_records[0].get("password_hash", "")

            # Verify password
            try:
                password_ok = pwd_context.verify(raw_pass, stored_hash)
            except Exception:
                log.exception("bcrypt verify error for user_id=%s", user_id)
                ui.notify("A server error occurred. Please try again.", type="negative")
                return

            if not password_ok:
                _record_failure(raw_user)
                ui.notify("Wrong username or password.", type="negative")
                return

            # --- Authentication successful ---
            _clear_failures(raw_user)

            roles = await _get_user_roles(api_client, user_id)

            # Create a DB-scoped JWT for PostgREST / RLS
            db_token = create_db_token(user["alias"], roles)

            now_utc = datetime.now(timezone.utc)

            app.storage.user.update(
                {
                    "username": user["alias"],
                    "user_id": user_id,
                    "authenticated": True,
                    "roles": roles,
                    "db_token": db_token,
                    # login_time enables the server-side 3-hour expiry check
                    # in AuthMiddleware (main.py). Without this the middleware
                    # can never enforce expiry.
                    "login_time": now_utc.isoformat(),
                }
            )

            log.info(
                "User '%s' (id=%s, roles=%s) logged in at %s",
                user["alias"],
                user_id,
                roles,
                now_utc.isoformat(),
            )

            ui.navigate.to(redirect_to)

        # ----------------------------------------------------------------
        # UI
        # ----------------------------------------------------------------
        with ui.card().classes("absolute-center"):
            ui.label("Gestión Sindicato Inquilinas de Madrid").classes(
                "text-h6 self-center"
            )
            username = (
                ui.input("Username")
                .props("autofocus")
                .on("keydown.enter", try_login)
            )
            password = (
                ui.input("Password", password=True, password_toggle_button=True)
                .on("keydown.enter", try_login)
            )
            ui.button("Log in", on_click=try_login)

        return None