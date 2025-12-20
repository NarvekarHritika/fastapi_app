from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import PostCreate, PostResponse
from app.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.images import imagekit
import os
import shutil
import tempfile
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    An asynchronous context manager for managing the application's lifespan.
    This function is executed when the application starts and shuts down.
    It ensures that the database and tables are created before the application starts accepting requests.
    """
    # On startup, create the database and tables if they don't already exist.
    await create_db_and_tables()
    # The 'yield' keyword passes control back to the application.
    yield


# Create a FastAPI app instance, with the lifespan context manager.
app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Handles file uploads.

    This endpoint accepts a file and a caption, uploads the file to ImageKit,
    and creates a new 'Post' record in the database with the file's metadata.

    Args:
        file: The file to upload.
        caption: The caption for the post.
        session: The database session, injected as a dependency.

    Returns:
        The newly created Post object.
    """
    # A temporary file path is used to store the uploaded file before uploading to ImageKit.
    temp_file_path = None

    try:
        # Create a temporary file to save the uploaded content.
        # 'delete=False' is important to be able to read it later.
        # The suffix is preserved to maintain the file extension.
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            temp_file_path = temp_file.name
            # Copy the uploaded file's content to the temporary file.
            shutil.copyfileobj(file.file, temp_file)

            # Upload the file to ImageKit from the temporary path.
            upload_result = imagekit.files.upload(
                file=open(temp_file_path, "rb"),
                file_name=file.filename,
                tags=["backend-upload"],
                use_unique_file_name=True,
            )

            # Determine the file type based on the file's content type.
            file_type = "video" if file.filename.startswith("video/") else "image"

            # Create a new Post object with the data from the upload.
            post = Post(
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
        # If any exception occurs, raise an HTTP 500 error.
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # This block ensures that the temporary file is always cleaned up.
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        # Close the uploaded file.
        file.file.close()


@app.get("/feed")
async def feed(session: AsyncSession = Depends(get_async_session)):
    """
    Retrieves a feed of all posts from the database.

    Args:
        session: The database session, injected as a dependency.

    Returns:
        A dictionary containing a list of all posts, ordered by creation date.
    """
    # Execute a query to select all posts, ordered by creation date in descending order.
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    # Extract the Post objects from the result.
    posts = [row[0] for row in result.all()]
    # Create a list of dictionaries with post data for the response.
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
            }
        )

    return {"posts": posts_data}


@app.delete("/delete/{post_id}")
async def delete_post(post_id: str, session: AsyncSession = Depends(get_async_session)):
    """
    Deletes a post from the database.

    Args:
        post_id: The ID of the post to delete.
        session: The database session, injected as a dependency.

    Returns:
        A dictionary with a success message.
    """
    try:
        # Convert the post_id string to a UUID object.
        post_id = uuid.UUID(post_id)
        # Find the post in the database by its ID.
        result = await session.execute(select(Post).where(Post.id == post_id))
        post = result.scalars().first()
        # If the post is not found, raise a 404 error.
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Delete the post from the database.
        await session.delete(post)
        # Commit the transaction.
        await session.commit()
        return {"success": True, "message": "Post deleted successfully"}
    except Exception as e:
        # If any exception occurs, raise an HTTP 500 error.
        raise HTTPException(status_code=500, detail=str(e))
