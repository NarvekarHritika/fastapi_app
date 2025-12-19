from fastapi import FastAPI, HTTPException
from app.schemas import PostCreate, PostResponse

app = FastAPI()
text_posts = {
    1: {
        "title": "Today's Weather so lovely",
        "content": "Today is a sunny day which makes it perfect to go for a picnic",
    },
    2: {
        "title": "My Favorite Recipe",
        "content": "I'm sharing my favorite chocolate chip cookie recipe today!",
    },
    3: {
        "title": "Book Recommendation",
        "content": "Just finished reading 'The Midnight Library' and I highly recommend it.",
    },
    4: {
        "title": "Productivity Tips",
        "content": "Here are 5 tips to help you stay focused and productive while working from home.",
    },
    5: {
        "title": "Travel Diary: Japan",
        "content": "Exploring the beautiful temples of Kyoto was a breathtaking experience.",
    },
    6: {
        "title": "Learning a New Language",
        "content": "I've been learning Spanish for 3 months now, and it's been a rewarding journey.",
    },
    7: {
        "title": "Movie Review: Dune Part Two",
        "content": "A visually stunning sci-fi epic that lives up to the hype.",
    },
    8: {
        "title": "My Morning Routine",
        "content": "How I start my day for a productive and positive mindset.",
    },
    9: {
        "title": "Gardening Update",
        "content": "My tomato plants are finally starting to bear fruit!",
    },
    10: {
        "title": "A Funny Story",
        "content": "Let me tell you about the time I accidentally wore two different shoes to work.",
    },
}


@app.get("/posts")
def get_all_posts(limit: int = None):
    if limit:
        return list(text_posts.values())[:limit]
    return text_posts
    # this should be pydentic object or python object, Python Dict is almost eqivalent to JSON object


@app.get("/posts/{post_id}")
def get_post(post_id: int) -> PostResponse:
    if post_id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")
    return text_posts.get(post_id)


@app.post("/posts")
def create_post(post: PostCreate) -> PostResponse:
    new_post = {"title": post.title, "content": post.content}
    post_id = len(text_posts) + 1
    text_posts[post_id] = new_post
    return new_post
