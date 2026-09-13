from __future__ import annotations


def test_status_defaults_to_unauthenticated(client):
    resp = client.get("/api/auth/status")
    assert resp.status_code == 200
    assert resp.json() == {"authenticated": False}


def test_login_wrong_password_rejected(client):
    resp = client.post("/api/auth/login", json={"password": "definitely-wrong"})
    assert resp.status_code == 401

    # A failed login must not authenticate the session.
    status = client.get("/api/auth/status")
    assert status.json() == {"authenticated": False}


def test_login_correct_password_sets_session_cookie(client):
    resp = client.post("/api/auth/login", json={"password": "test-password"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert "session_token" in resp.cookies

    status = client.get("/api/auth/status")
    assert status.status_code == 200
    assert status.json() == {"authenticated": True}


def test_logout_clears_session(client):
    login = client.post("/api/auth/login", json={"password": "test-password"})
    assert login.status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert logout.json() == {"status": "ok"}

    status = client.get("/api/auth/status")
    assert status.json() == {"authenticated": False}


def test_logout_without_session_requires_auth(client):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 401
    assert resp.json() == {"error": "unauthenticated"}


def test_devices_route_401_body_matches_contract(client):
    resp = client.get("/api/devices")
    assert resp.status_code == 401
    assert resp.json() == {"error": "unauthenticated"}
