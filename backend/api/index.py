import traceback
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

# Try to import the real app; fall back to an error app on import failure
_import_error = None
try:
    from app.main import app
except Exception as _e:
    _import_error = traceback.format_exc()
    app = FastAPI()

    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def _error_handler(path: str = ""):
        return PlainTextResponse(
            f"Import error:\n{_import_error}", status_code=500
        )
