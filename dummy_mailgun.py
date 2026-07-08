"""
Dummy Mailgun server for local development.

The app sends emails through Mailgun's HTTP API, which needs a paid account.
This tiny server mimics the single endpoint the app actually uses
(POST /v3/{domain}/messages) so you can run and test the whole registration /
email-confirmation flow locally without sending — or paying for — real email.

Instead of delivering anything it just logs the message to the console.

Run it (in its own terminal):

    uvicorn dummy_mailgun:app --port 8001
    # or simply
    python dummy_mailgun.py

Then point the app at it in your .env (dev):

    DEV_MAILGUN_API_URL=http://localhost:8001/v3
    DEV_MAILGUN_DOMAIN=sandbox.example.org
    DEV_MAILGUN_API_KEY=dummy-key
"""

import logging
from typing import List

import uvicorn
from fastapi import FastAPI, Form

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("dummy_mailgun")

app = FastAPI(title="Dummy Mailgun")


@app.post("/v3/{domain}/messages")
async def send_message(
    domain: str,
    to: List[str] = Form(default=[]),
    subject: str = Form(default=""),
    text: str = Form(default=""),
    from_: str = Form(default="", alias="from"),
):
    """Accept a Mailgun-style message and log it instead of sending it."""
    logger.info("=" * 70)
    logger.info("📧  Dummy Mailgun received an email (not actually sent)")
    logger.info("  domain : %s", domain)
    logger.info("  from   : %s", from_)
    logger.info("  to     : %s", ", ".join(to))
    logger.info("  subject: %s", subject)
    logger.info("  body   :")
    for line in text.splitlines() or [text]:
        logger.info("    %s", line)
    logger.info("=" * 70)

    # Mirror the shape of a real Mailgun success response.
    return {"id": "<dummy.mailgun.local>", "message": "Queued. Thank you."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
