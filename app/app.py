from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import UserRead, UserCreate, UserUpdate
from app.db import Post, create_db_and_tables, get_async_session, User
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.images import imagekit
import os
import shutil
import tempfile
import uuid

from app.users import fastapi_users, auth_backend, current_active_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager to handle application startup and shutdown events.
    This function ensures that the database and its tables are created before the
    application starts serving requests.
    """
    # On startup, create the database and tables if they don't already exist.
    await create_db_and_tables()
    # 'yield' transfers control back to the application.
    yield


# Create a FastAPI app instance with the lifespan context manager.
app = FastAPI(lifespan=lifespan)

# Add CORS Middleware
# This allows requests from browsers (even if running on different ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers for different functionalities.
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(
    fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(current_active_user),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Handles file uploads, storing them in ImageKit and creating a 'Post' record.
    This endpoint accepts a file and an optional caption. The file is uploaded to
    ImageKit, and a new 'Post' entry is created in the database with the file's
    metadata and the user's caption.
    Args:
        file: The file to be uploaded (image or video).
        user: The currently authenticated user, obtained from the dependency.
        caption: An optional caption for the post.
        session: The database session, injected as a dependency.
    Returns:
        The newly created Post object, including its database ID and timestamp.
    """
    temp_file_path = None
    try:
        # Create a temporary file to save the uploaded content.
        # 'delete=False' is important to be able to read it later.
        # The suffix is preserved to maintain the file extension.
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

            # Upload the file to ImageKit.
            upload_result = imagekit.files.upload(
                file=open(temp_file_path, "rb"),
                file_name=file.filename,
                tags=["backend-upload"],
                use_unique_file_name=True,
            )

            # Determine if the file is a video or an image based on its content type.
            file_type = "video" if file.content_type.startswith("video/") else "image"

            # Create a new Post with the uploaded file's data.
            post = Post(
                user_id=user.id,
                caption=caption,
                url=upload_result.url,
                file_type=file_type,
                file_name=upload_result.name,
            )

            # Add the new Post to the database session.
            session.add(post)
            # Commit the changes to the database.
            await session.commit()
            # Refresh the 'post' object to get the latest data from the database (e.g., id, created_at).
            await session.refresh(post)
            return post
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file and close the uploaded file.
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()


@app.get("/feed")
async def get_feed(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Retrieves a feed of all posts, ordered by creation date.
    Args:
        user: The currently authenticated user, for future personalization.
        session: The database session, injected as a dependency.
    Returns:
        A dictionary containing a list of all posts, with detailed information
        for each post, including whether the current user is the owner.
    """
    # Query for all posts, ordered from newest to oldest.
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    # Format the posts data for the response.
    posts_data = []
    for post in posts:
        posts_data.append(
            {
                "id": str(post.id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
                "is_owner": post.user_id == user.id,
                "email": user.email,
            }
        )

    return {"posts": posts_data}


@app.delete("/delete/{post_id}")
async def delete_post(
    post_id: str,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Deletes a specific post by its ID.
    Args:
        post_id: The ID of the post to be deleted.
        user: The currently authenticated user, for ownership verification.
        session: The database session, injected as a dependency.
    Returns:
        A confirmation message upon successful deletion.
    """
    try:
        post_id_uuid = uuid.UUID(post_id)
        # Retrieve the post by its ID.
        result = await session.execute(select(Post).where(Post.id == post_id_uuid))
        post = result.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Verify that the current user is the owner of the post.
        if post.user_id != user.id:
            raise HTTPException(
                status_code=403, detail="You do not have permission to delete this post"
            )
        # Delete the post and commit the change.
        await session.delete(post)
        await session.commit()
        return {"success": True, "message": "Post deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

app.mount("/", StaticFiles(directory="static", html=True), name="root")