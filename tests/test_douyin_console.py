from fastapi.testclient import TestClient

from builder.douyin_auth import DouyinAuth
from signing.douyin_abogus import encode_a_bogus
from web.actions import ACTIONS
from web.app import app


def test_a_bogus_is_opaque_and_stable_enough():
    token = encode_a_bogus(query="aid=6383&keyword=test", user_agent=DouyinAuth.UA)
    assert isinstance(token, str) and len(token) >= 32
    assert "=" not in token


def test_cookie_session_summary():
    auth = DouyinAuth.from_cookie(
        "sessionid=123_abc; ttwid=1%7Cdemo; msToken=abc; UIFID=uif; s_v_web_id=verify_x"
    )
    assert auth.logged_in
    summary = auth.summary()
    assert summary["has_ms_token"]
    assert summary["has_uifid"]
    assert "sessionid" in summary["cookie_names"]


def test_console_import_and_catalog():
    client = TestClient(app)
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["actions"] == len(ACTIONS)
    page = client.get("/")
    assert page.status_code == 200
    assert "Douyin" in page.text
    imported = client.post("/api/session", json={
        "cookie": "sessionid=1_x; msToken=token; UIFID=abc; ttwid=tt",
    })
    assert imported.status_code == 200
    body = imported.json()
    assert body["imported"] is True
    assert body["logged_in"] is True
    status = client.get("/api/session")
    assert status.json()["imported"] is True
    missing = client.post("/api/call", json={"action": "not_a_method", "args": {}})
    assert missing.status_code == 400
    cleared = client.delete("/api/session")
    assert cleared.json()["imported"] is False
