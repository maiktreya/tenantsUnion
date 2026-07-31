# build/niceGUI/auth/login.py

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi.responses import RedirectResponse
from nicegui import app, ui

from api.client import APIClient
from auth.token_utils import create_db_token

log = logging.getLogger(__name__)

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


async def _verify_login(
    api_client: APIClient, alias: str, password: str
) -> Optional[dict]:
    """Call the SECURITY DEFINER RPC `rpc_login` once and return its row.

    Returns None on any failure (unknown user, inactive account, missing
    credentials row, wrong password, RPC unavailable, network error). The
    bcrypt verification happens server-side via pgcrypto, so the
    unauthenticated login flow no longer has to read `usuarios` /
    `usuario_credenciales` / `usuario_roles` / `roles` directly as
    web_anon — those reads are now RLS-gated and the only anonymous entry
    point is this RPC.

    The result (if not None) is the single dict returned by the RPC:
        {"user_id": int, "alias": str, "roles": [str, ...]}
    """
    try:
        result = await api_client.call_rpc(
            "rpc_login",
            {"p_alias": alias, "p_password": password},
        )
    except Exception:
        log.exception("rpc_login call failed for alias=%s", alias)
        return None

    if not result:
        # No rows returned == login failure (server verified and declined).
        return None

    # PostgREST serializes a SETOF composite as a JSON array; the
    # `call_rpc` helper returns the raw JSON. Normalise both shapes.
    if isinstance(result, list):
        return result[0] if result else None
    return result


# =====================================================================
# PAGE FACTORY
# =====================================================================

def create_login_page(api_client: APIClient):
    """Register the /login page with NiceGUI."""

    @ui.page("/login")
    async def login_page(redirect_to: str = "/") -> Optional[RedirectResponse]:

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

            try:
                result = await _verify_login(api_client, raw_user, raw_pass)
            except Exception:
                log.exception("Login RPC error for alias=%s", raw_user)
                ui.notify("A server error occurred. Please try again.", type="negative")
                return

            if not result:
                # Single failure path for every reason (unknown user /
                # inactive / no creds row / wrong password / RPC missing).
                # The brute-force guard treats them all the same way.
                _record_failure(raw_user)
                ui.notify("Wrong username or password.", type="negative")
                return

            _clear_failures(raw_user)

            user_id: int = int(result["user_id"])
            user_alias: str = result["alias"]
            roles: List[str] = result.get("roles") or []
            db_token = create_db_token(user_id, user_alias, roles)
            now_utc = datetime.now(timezone.utc)

            app.storage.user.update(
                {
                    "username": user_alias,
                    "user_id": user_id,
                    "authenticated": True,
                    "roles": roles,
                    "db_token": db_token,
                    "login_time": now_utc.isoformat(),
                }
            )

            log.info(
                "User '%s' (id=%s, roles=%s) logged in at %s",
                user_alias,
                user_id,
                roles,
                now_utc.isoformat(),
            )

            ui.navigate.to(redirect_to)

        # ----------------------------------------------------------------
        # UI (REFACTORED WITH DYNAMIC INSTANCE TEXT HOOKS)
        # ----------------------------------------------------------------
        with ui.card().classes("absolute-center"):
            instance_text = os.environ.get("INSTANCE_NAME", "Madrid")
            ui.label(f"Gestión Sindicato Inquilinas {instance_text}").classes(
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