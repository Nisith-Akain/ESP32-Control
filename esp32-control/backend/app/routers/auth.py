"""`/api/auth/*` endpoints per TEAM/INTERFACES.md Section 12.1."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from ..auth import (
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    create_session,
    invalidate_session,
    is_valid_session,
    require_session,
    set_session_cookie,
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class StatusOrOkResponse(BaseModel):
    status: str = "ok"


class StatusResponse(BaseModel):
    authenticated: bool


@router.post("/login", response_model=StatusOrOkResponse)
def login(payload: LoginRequest, response: Response) -> StatusOrOkResponse:
    if payload.password != settings.ui_password:
        raise HTTPException(status_code=401, detail="invalid password")
    token = create_session()
    set_session_cookie(response, token)
    return StatusOrOkResponse(status="ok")


@router.post("/logout", response_model=StatusOrOkResponse, dependencies=[Depends(require_session)])
def logout(request: Request, response: Response) -> StatusOrOkResponse:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    invalidate_session(token)
    clear_session_cookie(response)
    return StatusOrOkResponse(status="ok")


@router.get("/status", response_model=StatusResponse)
def status(request: Request) -> StatusResponse:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return StatusResponse(authenticated=is_valid_session(token))
