"""
Auth compatibility routes — minimal auth endpoints for the
Jana Sunuwaai frontend.

Endpoints:
    POST /api/v1/auth/register — register a new user
    POST /api/v1/auth/login    — login and get a JWT-like token
    POST /api/v1/auth/refresh  — refresh token
    POST /api/v1/auth/logout   — logout
    GET  /api/v1/users/me      — get current user profile
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["Auth"])


# ── Schemas ─────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    avatar: Optional[str] = None
    role: str = "citizen"
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


# ── In-memory user store ────────────────────────────────────────
_users: dict = {}
_next_uid = 1

# Seed a default user
DEFAULT_USER = UserResponse(
    id=1,
    name="Test User",
    email="test@janasunuwaai.np",
    avatar=None,
    role="citizen",
    created_at=datetime.now().isoformat(),
)
_users["test@janasunuwaai.np"] = {
    "user": DEFAULT_USER,
    "password": "password123",
}
_next_uid = 2


# ── Endpoints ───────────────────────────────────────────────────
@router.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest):
    """Register a new user."""
    global _next_uid
    if body.email in _users:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = UserResponse(
        id=_next_uid,
        name=body.name,
        email=body.email,
        created_at=datetime.now().isoformat(),
    )
    _users[body.email] = {"user": user, "password": body.password}
    _next_uid += 1
    return AuthResponse(token=f"jwt-token-{user.id}", user=user)


@router.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest):
    """Login with email and password."""
    entry = _users.get(body.email)
    if not entry or entry["password"] != body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(token=f"jwt-token-{entry['user'].id}", user=entry["user"])


@router.post("/auth/refresh")
def refresh():
    """Refresh auth token (stub)."""
    return {"token": "jwt-token-refreshed", "message": "Token refreshed"}


@router.post("/auth/logout")
def logout():
    """Logout (stub)."""
    return {"message": "Logged out successfully"}


@router.get("/users/me", response_model=UserResponse)
def get_current_user():
    """Get the current user profile (returns default user for now)."""
    return DEFAULT_USER
