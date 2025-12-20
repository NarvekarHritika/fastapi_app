"""
This module defines the database models and asynchronous connection settings
for the application using SQLAlchemy.

It includes the `User` and `Post` models, which represent the application's core
data structures. It also provides utility functions for creating the database
and tables, and for managing database sessions within a FastAPI application.
"""

from collections.abc import AsyncGenerator
import uuid
import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from fastapi_users.db import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi import Depends

# Define the database URL for connecting to a SQLite database.
# The database file will be named 'test.db' in the current directory.
# 'aiosqlite' is the driver that allows asynchronous operations.
DATABASE_URL = "sqlite+aiosqlite:///./test.db"


# Create a base class for declarative models in SQLAlchemy.
# All ORM models in the application will inherit from this class, allowing them
# to be discovered and managed by SQLAlchemy's ORM system.
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    Represents a user in the database.

    This model inherits from `SQLAlchemyBaseUserTableUUID` to include the default
    user fields provided by `fastapi-users` (e.g., email, hashed_password).
    It also inherits from `Base` to be part of the SQLAlchemy declarative base.

    Attributes:
        posts: A one-to-many relationship to the `Post` model, representing all
               the posts created by this user. The `back_populates` argument
               ensures that this relationship is bidirectionally linked with the
               `user` relationship on the `Post` model.
    """

    posts = relationship(argument="Post", back_populates="user")


class Post(Base):
    """
    Represents a user-created post in the database.

    Each post is linked to a user and contains information about an uploaded file,
    such as an image or video.

    Attributes:
        id: The primary key of the post, a UUID to ensure global uniqueness.
        user_id: A foreign key to the `user` table, linking the post to its creator.
        caption: A text field for the post's caption.
        url: The URL of the image or video file, typically hosted on a CDN.
        file_type: The type of the file (e.g., 'image', 'video').
        file_name: The name of the uploaded file.
        created_at: The timestamp when the post was created, defaults to the
                    current UTC time.
        user: A many-to-one relationship to the `User` model, representing the
              user who created the post. The `back_populates` argument ensures
              bidirectional linking with the `posts` relationship on the `User`
              model.
    """

    __tablename__ = "posts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    caption = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship(argument="User", back_populates="posts")


# Create an asynchronous engine for the specified database URL.
# The engine manages the connection pool and dialect for the database.
engine = create_async_engine(DATABASE_URL)
# Create a session maker that will be used to create new asynchronous sessions.
# `expire_on_commit=False` is set to prevent SQLAlchemy from expiring loaded
# objects after a transaction is committed. This is important in an async
# context, especially with FastAPI, where you might access object properties
# after the session has been committed and closed.
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    """
    Creates all database tables defined by the models that inherit from `Base`.

    This function should be called during application startup to ensure that the
    database schema is up-to-date.
    """
    async with engine.begin() as conn:
        # This command runs the SQLAlchemy `create_all` method, which generates
        # the necessary SQL to create all tables that do not already exist.
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    An asynchronous generator that provides a database session for a single request.

    This function is designed to be used as a FastAPI dependency. It creates a new
    `AsyncSession` for each incoming request and ensures that it is properly
    closed afterward.

    Yields:
        An `AsyncSession` object that can be used to interact with the database.
    """
    # A new session is created from the session maker for each request.
    async with async_session_maker() as session:
        # The session is yielded to the endpoint/calling function.
        yield session
        # The session is automatically closed when the `async with` block is exited.


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """
    A FastAPI dependency that provides a user database instance.

    This function takes an `AsyncSession` and provides a `SQLAlchemyUserDatabase`
    adapter, which is used by `fastapi-users` to manage user-related database
    operations.

    Args:
        session: The database session, injected by FastAPI.

    Yields:
        A `SQLAlchemyUserDatabase` instance configured with the `User` model.
    """
    yield SQLAlchemyUserDatabase(session, User)
