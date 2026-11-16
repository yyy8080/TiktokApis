"""Ordered Douyin web query builder."""

from __future__ import annotations

from collections import OrderedDict
from urllib.parse import quote

from builder.douyin_auth import DouyinAuth
from signing.douyin_abogus import encode_a_bogus


class DouyinParams:
    def __init__(self, values=None):
        self.params = OrderedDict()
        source = values.items() if hasattr(values, "items") else (values or ())
        for key, value in source:
            self.add(key, value)

    def add(self, key, value):
        self.params[str(key)] = "" if value is None else str(value)
        return self

    def update(self, values):
        for key, value in values.items():
            self.add(key, value)
        return self

    def common(self, auth: DouyinAuth, *, extra=None):
        browser_version = "0"
        if "Chrome/" in auth.user_agent:
            browser_version = auth.user_agent.split("Chrome/", 1)[1].split(" ", 1)[0]
        values = OrderedDict([
            ("device_platform", "webapp"),
            ("aid", "6383"),
            ("channel", "channel_pc_web"),
            ("pc_client_type", "1"),
            ("pc_libra_divert", "Windows"),
            ("update_version_code", "170400"),
            ("support_h265", "1"),
            ("support_dash", "1"),
            ("version_code", "170400"),
            ("version_name", "17.4.0"),
            ("cookie_enabled", "true"),
            ("screen_width", auth.screen_width),
            ("screen_height", auth.screen_height),
            ("browser_language", "zh-CN"),
            ("browser_platform", "Win32"),
            ("browser_name", "Chrome"),
            ("browser_version", browser_version),
            ("browser_online", "true"),
            ("engine_name", "Blink"),
            ("engine_version", browser_version),
            ("os_name", "Windows"),
            ("os_version", "10"),
            ("cpu_core_num", auth.cpu_core_num),
            ("device_memory", auth.device_memory),
            ("platform", "PC"),
            ("downlink", "10"),
            ("effective_type", "4g"),
            ("round_trip_time", "50"),
        ])
        if auth.webid:
            values["webid"] = auth.webid
        if auth.uifid:
            values["uifid"] = auth.uifid
        if extra:
            values.update({str(key): str(value) for key, value in extra.items()})
        return self.update(values)

    def to_query(self) -> str:
        parts = []
        for key, value in self.params.items():
            parts.append(f"{quote(str(key), safe='-_.~')}={quote(str(value), safe='-_.~')}")
        return "&".join(parts)

    def with_signature(self, auth: DouyinAuth, *, body: str | bytes = "") -> "DouyinParams":
        if auth.ms_token:
            self.add("msToken", auth.ms_token)
        unsigned = self.to_query()
        self.add("a_bogus", encode_a_bogus(
            query=unsigned, user_agent=auth.user_agent, body=body,
        ))
        return self
