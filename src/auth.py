"""Single-password session auth."""
import asyncio
import hmac

from fastapi import HTTPException, Request


def check_password(given: str, expected: str) -> bool:
    return hmac.compare_digest(given.encode(), expected.encode())


def require_auth(request: Request) -> None:
    if not request.session.get("auth"):
        raise HTTPException(401, "login required")


async def login(request: Request, password: str, expected: str) -> bool:
    if check_password(password, expected):
        request.session["auth"] = True
        return True
    await asyncio.sleep(1)  # slows brute force on the public IP
    return False
