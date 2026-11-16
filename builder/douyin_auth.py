"""Douyin web session state from a current browser Cookie header."""

from __future__ import annotations

from typing import Mapping
from urllib.parse import unquote

from builder.auth import CookieDict, _cookie_pair, _cookie_tokens


class DouyinEvidenceError(RuntimeError):
    """The Douyin request cannot be aligned with the current browser session."""


class DouyinAuth:
    """Reusable Douyin web session. The only acquisition path is ``from_cookie``."""

    UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    )
    SEC_CH_UA = '"Google Chrome";v="144", "Not_A Brand";v="8", "Chromium";v="144"'
    SEC_CH_UA_PLATFORM = '"Windows"'
    ACCEPT_LANGUAGE = "zh-CN,zh;q=0.9,en;q=0.8"

    def __init__(self, cookie: str | Mapping[str, str] | None = None, **runtime):
        self.cookie = CookieDict(owner=self)
        self._cookie_str = ""
        self.document_cookie = str(runtime.get("document_cookie") or "")
        self.device_id = str(runtime.get("device_id") or "")
        self.webid = str(runtime.get("webid") or "")
        self.user_agent = runtime.get("user_agent") or self.UA
        self.sec_ch_ua = runtime.get("sec_ch_ua") or self.SEC_CH_UA
        self.sec_ch_ua_platform = runtime.get("sec_ch_ua_platform") or self.SEC_CH_UA_PLATFORM
        self.accept_language = runtime.get("accept_language") or self.ACCEPT_LANGUAGE
        self.screen_width = str(runtime.get("screen_width") or "1920")
        self.screen_height = str(runtime.get("screen_height") or "1080")
        self.cpu_core_num = str(runtime.get("cpu_core_num") or "16")
        self.device_memory = str(runtime.get("device_memory") or "8")
        self.local_storage = dict(runtime.get("local_storage") or {})
        self.session_storage = dict(runtime.get("session_storage") or {})
        self.ticket_guard_private_key = runtime.get("ticket_guard_private_key", "")
        self.ticket_guard_encrypt_ticket = runtime.get("ticket_guard_encrypt_ticket", "")
        self.ticket_guard_ts_sign = runtime.get("ticket_guard_ts_sign", "")
        self.ticket_guard_version = runtime.get("ticket_guard_version", "1")
        self.ticket_guard_iteration_version = runtime.get("ticket_guard_iteration_version", "0")
        self.passport_csrf_token = runtime.get("passport_csrf_token", "")
        if cookie:
            self.set_cookie_header(cookie if isinstance(cookie, str) else None, cookie)
            if not self.passport_csrf_token:
                self.passport_csrf_token = unquote(self.cookie.get("passport_csrf_token", ""))
            if not self.webid:
                self.webid = self.cookie.get("webid", "") or self.local_storage.get("webid", "")
            if not self.device_id:
                self.device_id = self.cookie.get("ttwid", "")

    @classmethod
    def from_cookie(cls, cookie_str: str = "", **kwargs) -> "DouyinAuth":
        if not str(cookie_str or "").strip() and not kwargs.get("cookie"):
            raise DouyinEvidenceError("缺少 Douyin Cookie")
        return cls(cookie_str, **kwargs)

    @property
    def cookie_str(self) -> str:
        return self._cookie_str

    @property
    def ms_token(self) -> str:
        return (
            self.session_storage.get("msToken")
            or self.local_storage.get("msToken")
            or self.cookie.get("msToken", "")
        )

    @property
    def ttwid(self) -> str:
        return unquote(self.cookie.get("ttwid", ""))

    @property
    def uifid(self) -> str:
        return self.cookie.get("UIFID", "") or self.cookie.get("uifid", "")

    @property
    def verify_fp(self) -> str:
        return self.cookie.get("s_v_web_id", "")

    @property
    def logged_in(self) -> bool:
        return bool(
            self.cookie.get("sessionid")
            or self.cookie.get("sessionid_ss")
            or self.cookie.get("sid_tt")
            or self.cookie.get("sid_guard")
        )

    def uid(self) -> str:
        session = self.cookie.get("sessionid") or self.cookie.get("sessionid_ss") or ""
        if session and "_" in session:
            return session.split("_", 1)[0]
        return self.cookie.get("uid_tt", "")

    def set_cookie_header(self, cookie_header: str | None, cookie: Mapping[str, str] | None = None):
        self.cookie.clear()
        tokens: list[str] = []
        if cookie_header:
            tokens.extend(_cookie_tokens(cookie_header))
        elif cookie:
            if isinstance(cookie, str):
                tokens.extend(_cookie_tokens(cookie))
            else:
                tokens.extend(f"{key}={value}" for key, value in cookie.items())
        ordered: list[tuple[str, str]] = []
        for token in tokens:
            name, value = _cookie_pair(token)
            if name:
                ordered.append((name, value))
                self.cookie[name] = value
        self._cookie_str = "; ".join(f"{name}={value}" for name, value in ordered)

    def apply_set_cookie(self, headers):
        raw = headers.get("Set-Cookie") if hasattr(headers, "get") else None
        if not raw:
            get_all = getattr(headers, "get_all", None) or getattr(headers, "getlist", None)
            values = get_all("Set-Cookie") if get_all else []
        else:
            values = raw if isinstance(raw, list) else [raw]
        for item in values:
            pair = str(item).split(";", 1)[0]
            name, value = _cookie_pair(pair)
            if name:
                self.cookie[name] = value
        self._cookie_str = "; ".join(f"{key}={value}" for key, value in self.cookie.items())

    def require_cookie(self, *names: str):
        missing = [name for name in names if not self.cookie.get(name)]
        if missing:
            raise DouyinEvidenceError(f"缺少 Cookie 字段: {', '.join(missing)}")
        return self

    def require_session(self):
        if not self.logged_in:
            raise DouyinEvidenceError("Cookie 未包含已登录的 sessionid/sid_tt/sid_guard")
        return self

    def build_ticket_guard(self, path: str, *, timestamp: int | None = None) -> dict[str, str]:
        from signing.ticket_guard import build_headers
        missing = [
            name for name, value in (
                ("ticket_guard_private_key", self.ticket_guard_private_key),
                ("ticket_guard_encrypt_ticket", self.ticket_guard_encrypt_ticket),
                ("ticket_guard_ts_sign", self.ticket_guard_ts_sign),
            ) if not value
        ]
        if missing:
            raise DouyinEvidenceError(
                "缺少可重算 bd-ticket-guard 的 security-sdk 状态: " + ", ".join(missing)
            )
        headers = build_headers(
            private_key_pem=self.ticket_guard_private_key,
            encrypt_ticket=self.ticket_guard_encrypt_ticket,
            ts_sign=self.ticket_guard_ts_sign,
            path=path,
            timestamp=timestamp,
            version=self.ticket_guard_version or "1",
            iteration_version=self.ticket_guard_iteration_version or "0",
        )
        return {key.replace("tt-ticket-guard-", "bd-ticket-guard-"): value
                for key, value in headers.items()}

    def summary(self) -> dict[str, object]:
        cookie_names = list(self.cookie.keys())
        return {
            "logged_in": self.logged_in,
            "uid": self.uid(),
            "has_ms_token": bool(self.ms_token),
            "has_uifid": bool(self.uifid),
            "has_ttwid": bool(self.ttwid),
            "has_verify_fp": bool(self.verify_fp),
            "has_ticket_guard": bool(self.ticket_guard_private_key),
            "cookie_fields": len(cookie_names),
            "cookie_names": cookie_names,
            "user_agent": self.user_agent,
        }
