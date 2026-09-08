import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings
from .domain import StaffRole

_TOKEN_TTL = timedelta(hours=8)
_PASSWORD_ITERATIONS = 310_000
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class StaffUser:
    user_id: str
    email: str
    display_name: str
    role: StaffRole
    password_hash: str
    password_salt: str
    is_active: bool = True


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    password_salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        password_salt.encode(),
        _PASSWORD_ITERATIONS,
    ).hex()
    return password_salt, password_hash


def _seed_user(
    user_id: str,
    email: str,
    display_name: str,
    role: StaffRole,
) -> StaffUser:
    salt, password_hash = _hash_password(get_settings().demo_password)
    return StaffUser(user_id, email, display_name, role, password_hash, salt)


STAFF_USERS = [
    _seed_user(
        "staff-admin",
        "admin@autotrack.local",
        "AutoTrack Admin",
        StaffRole.ADMIN_MANAGER,
    ),
    _seed_user(
        "staff-advisor",
        "advisor@autotrack.local",
        "Service Advisor",
        StaffRole.SERVICE_ADVISOR,
    ),
    _seed_user(
        "staff-technician",
        "technician@autotrack.local",
        "Paint Technician",
        StaffRole.TECHNICIAN_PAINTER,
    ),
    _seed_user(
        "staff-viewer", "viewer@autotrack.local", "Read Only", StaffRole.READ_ONLY
    ),
]


def find_user(email: str) -> StaffUser | None:
    normalized_email = email.strip().lower()
    return next((user for user in STAFF_USERS if user.email == normalized_email), None)


def verify_password(password: str, user: StaffUser) -> bool:
    _, candidate_hash = _hash_password(password, user.password_salt)
    return hmac.compare_digest(candidate_hash, user.password_hash)


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user: StaffUser) -> str:
    expires_at = datetime.now(UTC) + _TOKEN_TTL
    payload = {
        "sub": user.user_id,
        "role": user.role.value,
        "exp": int(expires_at.timestamp()),
    }
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(
        get_settings().auth_secret.encode(),
        encoded_payload.encode(),
        hashlib.sha256,
    ).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> StaffUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        encoded_payload, encoded_signature = credentials.credentials.split(".", 1)
        expected_signature = hmac.new(
            get_settings().auth_secret.encode(),
            encoded_payload.encode(),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(_decode(encoded_signature), expected_signature):
            raise ValueError("invalid signature")
        payload = json.loads(_decode(encoded_payload))
        if int(payload["exp"]) <= int(datetime.now(UTC).timestamp()):
            raise ValueError("expired token")
        user = next(user for user in STAFF_USERS if user.user_id == payload["sub"])
        if not user.is_active or user.role.value != payload["role"]:
            raise ValueError("invalid user")
        return user
    except (ValueError, KeyError, StopIteration, TypeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The authentication token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def require_roles(*roles: StaffRole):
    def dependency(user: Annotated[StaffUser, Depends(get_current_user)]) -> StaffUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user

    return dependency
