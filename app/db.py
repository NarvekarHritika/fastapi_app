from collections.abc import AsyncGenerator
import uuid
import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from fastapi_users.db import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi import Depends

# Define the database URL for connecting to a SQLite database.
# The database file will be named 'test.db' in the current directory.
# 'aiosqlite' is the driver that allows asynchronous operations.
DATABASE_URL = "sqlite+aiosqlite:///./test.db"


# Create a base class for declarative models in SQLAlchemy.
# All ORM models will inherit from this class.
class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    posts = relationship(argument="Post", back_populates="user")


# Define the 'Post' model which corresponds to the 'posts' table in the database.
class Post(Base):
    __tablename__ = "posts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    caption = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship(argument="User", back_populates="posts")


# create DB:
# Create an asynchronous engine for the specified database URL.
# This engine manages the connection pool and dialect.
engine = create_async_engine(DATABASE_URL)
# Create a session maker that will be used to create new asynchronous sessions.
# 'expire_on_commit=False' prevents objects from being expired after a transaction is committed.
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


# An asynchronous function to create all database tables defined by the models
# that inherit from 'Base'.
async def create_db_and_tables():
    async with engine.begin() as conn:
        # This command runs the SQLAlchemy 'create_all' method, which generates
        # the necessary SQL to create the tables.
        await conn.run_sync(Base.metadata.create_all)


# An asynchronous generator function that provides a database session.
# This is typically used as a dependency in web frameworks like FastAPI.
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    # A new session is created from the session maker for each request.
    async with async_session_maker() as session:
        # The session is yielded to the calling function.
        yield session
        # The session is automatically closed when the 'with' block is exited.


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
