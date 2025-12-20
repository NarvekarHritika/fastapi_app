"""
This module defines the Pydantic schemas for data validation and serialization.

These schemas are used by FastAPI to validate incoming request bodies and to
format response data, ensuring that the data conforms to the expected structure and types.
"""

from pydantic import BaseModel
from fastapi_users import schemas
import uuid
import datetime


# class PostCreate(BaseModel):
#     """
#     Schema for creating a new post.

#     Attributes:
#         caption: The caption for the post, provided by the user.
#     """
#     caption: str


# class PostResponse(BaseModel):
#     """
#     Schema for representing a post in a response.

#     This schema is used to serialize the post data that is sent back to the client.

#     Attributes:
#         id: The unique identifier of the post.
#         user_id: The unique identifier of the user who created the post.
#         caption: The caption of the post.
#         url: The URL of the uploaded image or video.
#         file_type: The type of the file (e.g., 'image', 'video').
#         file_name: The name of the uploaded file.
#         created_at: The timestamp when the post was created.
#     """
#     id: uuid.UUID
#     user_id: uuid.UUID
#     caption: str
#     url: str
#     file_type: str
#     file_name: str
#     created_at: datetime.datetime

#     class Config:
#         """Pydantic configuration to allow creating the schema from an ORM model."""
#         # This allows Pydantic to create the schema from a SQLAlchemy model instance.
#         from_attributes = True


class UserRead(schemas.BaseUser[uuid.UUID]):
    """
    Schema for reading user information.

    Inherits from the base user schema provided by `fastapi-users` and is used
    to serialize user data when retrieving user information.
    """

    pass


class UserCreate(schemas.BaseUserCreate):
    """
    Schema for creating a new user.

    Inherits from the base user creation schema provided by `fastapi-users`.
    It defines the fields required to create a new user.
    """

    pass


class UserUpdate(schemas.BaseUserUpdate):
    """
    Schema for updating an existing user.

    Inherits from the base user update schema provided by `fastapi-users`.
    It defines the fields that can be updated for a user.
    """

    pass
