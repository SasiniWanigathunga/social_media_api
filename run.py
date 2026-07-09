"""Client script to exercise each Social Media API endpoint.

Start the API first (in another terminal):

    uvicorn social_media_api.main:app --reload

Then run this script:

    python run.py

Each function below calls exactly one endpoint and returns the parsed JSON
response. The `main()` demo chains them into a full user flow.
"""

import logging
import time

import httpx

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


def _auth(token: str) -> dict:
    """Build an Authorization header for endpoints that require login."""
    return {"Authorization": f"Bearer {token}"}


# --- user router ----------------------------------------------------------


def register(email: str, password: str) -> dict:
    """POST /register — create a new user account."""
    response = httpx.post(
        f"{BASE_URL}/register", json={"email": email, "password": password}
    )
    logger.info("register -> %s %s", response.status_code, response.json())
    return response.json()


def login(email: str, password: str) -> str:
    """POST /token — authenticate and return the access token."""
    response = httpx.post(
        f"{BASE_URL}/token", json={"email": email, "password": password}
    )
    logger.info("login -> %s %s", response.status_code, response.json())
    return response.json()["access_token"]


def confirm_email(token: str) -> dict:
    """GET /confirm/{token} — confirm a user's email with a confirmation token."""
    response = httpx.get(f"{BASE_URL}/confirm/{token}")
    logger.info("confirm_email -> %s %s", response.status_code, response.json())
    return response.json()


# --- post router ----------------------------------------------------------


def create_post(content: str, token: str, prompt: str = None) -> dict:
    """POST /posts — create a post; pass `prompt` to also generate an image."""
    params = {"prompt": prompt} if prompt else None
    response = httpx.post(
        f"{BASE_URL}/posts",
        json={"content": content},
        params=params,
        headers=_auth(token),
    )
    logger.info("create_post -> %s %s", response.status_code, response.json())
    return response.json()


def get_posts(sorting: str = "newest") -> list:
    """GET /posts — list posts sorted by newest / oldest / most_liked."""
    response = httpx.get(f"{BASE_URL}/posts", params={"sorting": sorting})
    logger.info("get_posts -> %s %s", response.status_code, response.json())
    return response.json()


def create_comment(comments: str, post_id: int, token: str) -> dict:
    """POST /comments — add a comment to a post."""
    response = httpx.post(
        f"{BASE_URL}/comments",
        json={"comments": comments, "post_id": post_id},
        headers=_auth(token),
    )
    logger.info("create_comment -> %s %s", response.status_code, response.json())
    return response.json()


def get_comments_for_post(post_id: int) -> list:
    """GET /posts/{post_id}/comments — list all comments on a post."""
    response = httpx.get(f"{BASE_URL}/posts/{post_id}/comments")
    logger.info("get_comments_for_post -> %s %s", response.status_code, response.json())
    return response.json()


def get_post_with_comments(post_id: int) -> dict:
    """GET /posts/{post_id} — fetch a post together with its comments."""
    response = httpx.get(f"{BASE_URL}/posts/{post_id}")
    logger.info("get_post_with_comments -> %s %s", response.status_code, response.json())
    return response.json()


def like_post(post_id: int, token: str) -> dict:
    """POST /like — like a post."""
    response = httpx.post(
        f"{BASE_URL}/like", json={"post_id": post_id}, headers=_auth(token)
    )
    logger.info("like_post -> %s %s", response.status_code, response.json())
    return response.json()


# --- helpers --------------------------------------------------------------


def wait_for_image_url(post_id: int, retries: int = 20, delay: float = 2.0) -> str | None:
    """Poll GET /posts/{post_id} until the background task fills in image_url.

    Returns the URL once available, or None if it never appears within
    `retries * delay` seconds (e.g. generation failed).
    """
    for attempt in range(1, retries + 1):
        image_url = get_post_with_comments(post_id)["post"]["image_url"]
        if image_url:
            logger.info("image ready after %s attempt(s): %s", attempt, image_url)
            return image_url
        logger.info("image not ready yet (attempt %s/%s)...", attempt, retries)
        time.sleep(delay)
    logger.info("image_url never populated — generation may have failed")
    return None


# --- upload router --------------------------------------------------------


def upload_file(file_path: str) -> dict:
    """POST /upload — upload a file to Backblaze B2."""
    with open(file_path, "rb") as f:
        response = httpx.post(f"{BASE_URL}/upload", files={"file": f})
    logger.info("upload_file -> %s %s", response.status_code, response.json())
    return response.json()


# --- demo flow ------------------------------------------------------------


def main():
    """Exercise the endpoints end to end against a running server."""
    email, password = "demo@example.com", "supersecret"

    register(email, password)
    token = login(email, password)

    prompt = "A cute creature with big eyes and a fluffy tail"

    post = create_post("Hello from run.py!", token, prompt=prompt)
    post_id = post["id"]

    # image_url is None on creation — the background task fills it in shortly.
    image_url = wait_for_image_url(post_id)
    logger.info("final image_url: %s", image_url)

    # create_comment("Nice post!", post_id, token)
    # like_post(post_id, token)

    # get_posts(sorting="most_liked")
    # get_comments_for_post(post_id)
    # get_post_with_comments(post_id)


if __name__ == "__main__":
    main()
