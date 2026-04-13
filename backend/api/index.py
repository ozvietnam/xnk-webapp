import sys
import traceback

try:
    from app.main import app
except Exception as e:
    # Expose import error as a minimal ASGI app so Vercel shows the real error
    tb = traceback.format_exc()
    async def app(scope, receive, send):
        if scope["type"] == "http":
            body = f"Import error: {e}\n\n{tb}".encode()
            await send({"type": "http.response.start", "status": 500,
                        "headers": [[b"content-type", b"text/plain"]]})
            await send({"type": "http.response.body", "body": body})
