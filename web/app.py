"""Local Douyin cookie console.

Sessions stay in process memory. Cookie strings are never written back to the
browser after import, and JSON logs omit the raw Cookie header.
"""

from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api.douyin_web import DouyinWebAPI
from builder.douyin_auth import DouyinAuth, DouyinEvidenceError
from web.actions import ACTIONS, run_action


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
SESSIONS: dict[str, dict[str, Any]] = {}
COOKIE_NAME = "dy_console"
app = FastAPI(title="Douyin Console", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class SessionIn(BaseModel):
    cookie: str = Field(..., min_length=8)
    user_agent: str = ""
    document_cookie: str = ""
    device_id: str = ""
    webid: str = ""
    ticket_guard_private_key: str = ""
    ticket_guard_encrypt_ticket: str = ""
    ticket_guard_ts_sign: str = ""


class CallIn(BaseModel):
    action: str
    args: dict[str, Any] = Field(default_factory=dict)


def _session(token: str | None):
    if not token or token not in SESSIONS:
        raise HTTPException(status_code=401, detail="请先导入 Cookie")
    return SESSIONS[token]


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "sessions": len(SESSIONS), "actions": len(ACTIONS)}


@app.get("/api/actions")
def list_actions():
    return {"actions": ACTIONS}


@app.get("/api/session")
def session_status(dy_console: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    if not dy_console or dy_console not in SESSIONS:
        return {"imported": False}
    return {"imported": True, "summary": SESSIONS[dy_console]["auth"].summary()}


@app.post("/api/session")
def import_session(body: SessionIn, response: Response):
    try:
        auth = DouyinAuth.from_cookie(
            body.cookie,
            user_agent=body.user_agent,
            document_cookie=body.document_cookie,
            device_id=body.device_id,
            webid=body.webid,
            ticket_guard_private_key=body.ticket_guard_private_key,
            ticket_guard_encrypt_ticket=body.ticket_guard_encrypt_ticket,
            ticket_guard_ts_sign=body.ticket_guard_ts_sign,
        )
    except DouyinEvidenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    token = secrets.token_urlsafe(24)
    SESSIONS[token] = {"auth": auth}
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, samesite="lax", max_age=12 * 3600,
    )
    return {"imported": True, "logged_in": auth.logged_in, "summary": auth.summary()}


@app.delete("/api/session")
def clear_session(response: Response, dy_console: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    if dy_console:
        SESSIONS.pop(dy_console, None)
    response.delete_cookie(COOKIE_NAME)
    return {"imported": False}


@app.post("/api/call")
def call_action(body: CallIn, dy_console: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    session = _session(dy_console)
    api = DouyinWebAPI(session["auth"])
    try:
        result = run_action(api, body.action, body.args)
    except (DouyinEvidenceError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except Exception as exc:
        return JSONResponse(
            {"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]},
            status_code=502,
        )
    return {"ok": True, "result": result}


@app.post("/api/publish")
async def publish(
    kind: str = Form(...),
    text: str = Form(...),
    title: str = Form(""),
    visibility_type: int = Form(1),
    dy_console: str | None = Cookie(default=None, alias=COOKIE_NAME),
    files: list[UploadFile] = File(...),
):
    session = _session(dy_console)
    api = DouyinWebAPI(session["auth"])
    saved: list[str] = []
    try:
        for item in files:
            suffix = Path(item.filename or "upload.bin").suffix
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            handle.write(await item.read())
            handle.close()
            saved.append(handle.name)
        if kind == "video":
            result = api.creator_publish(saved[0], text, visibility_type=visibility_type)
        elif kind == "photos":
            result = api.creator_publish_photos(saved, text, title=title, visibility_type=visibility_type)
        else:
            raise HTTPException(status_code=400, detail="kind 必须是 video 或 photos")
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse(
            {"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]},
            status_code=502,
        )
    finally:
        for path in saved:
            try:
                os.unlink(path)
            except OSError:
                pass
    return {"ok": True, "result": result}


def main():
    import uvicorn
    uvicorn.run(
        "web.app:app",
        host=os.environ.get("DOUYIN_CONSOLE_HOST", "127.0.0.1"),
        port=int(os.environ.get("DOUYIN_CONSOLE_PORT", "8787")),
        reload=False,
    )


if __name__ == "__main__":
    main()
