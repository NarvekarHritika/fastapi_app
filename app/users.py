import uuid
from typing import Optional
from dotenv import load_dotenv

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from app.db import User, get_user_db
import os

load_dotenv()

SECRET = os.getenv("SECRET_KEY")


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    Custom user manager for the application.
    This class provides the business logic for user management, including password resets
    and email verification. It hooks into the registration and password recovery
    processes to add custom logic, such as printing registration details.
    """

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """
        Hook that runs after a user is registered.
        """
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """
        Hook that runs after a user has requested a password reset.
        """
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """
        Hook that runs after a user has requested email verification.
        """
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """
    Dependency to get the user manager.
    This function provides the `UserManager` to the FastAPI application, with the
    user database injected as a dependency.
    """
    yield UserManager(user_db)


# Bearer token transport for authentication.
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    """
    Returns the JWT strategy for encoding and decoding tokens.
    """
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


# Authentication backend using JWT.
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Main object for FastAPI Users integration.
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Dependency to get the current active user.
current_active_user = fastapi_users.current_user(active=True)
