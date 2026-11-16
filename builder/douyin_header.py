"""Chrome-shaped Douyin web headers."""

from __future__ import annotations

from builder.header import Header, HeaderType
from builder.douyin_auth import DouyinAuth


class DouyinHeaderBuilder:
    @staticmethod
    def build(header_type: HeaderType, auth: DouyinAuth, *, referer: str,
              origin: str = "", sec_fetch_site: str = "same-origin") -> Header:
        h = Header()
        if header_type == HeaderType.DOC:
            h.set_header("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
            h.set_header("accept-language", auth.accept_language)
            h.set_header("cache-control", "no-cache")
            h.set_header("pragma", "no-cache")
            h.set_header("referer", referer)
            h.set_header("sec-ch-ua", auth.sec_ch_ua)
            h.set_header("sec-ch-ua-mobile", "?0")
            h.set_header("sec-ch-ua-platform", auth.sec_ch_ua_platform)
            h.set_header("sec-fetch-dest", "document")
            h.set_header("sec-fetch-mode", "navigate")
            h.set_header("sec-fetch-site", "none")
            h.set_header("upgrade-insecure-requests", "1")
            h.set_header("user-agent", auth.user_agent)
            h.set_header("cookie", auth.cookie_str)
            return h

        h.set_header("accept", "application/json, text/plain, */*")
        h.set_header("accept-language", auth.accept_language)
        h.set_header("referer", referer)
        h.set_header("sec-ch-ua", auth.sec_ch_ua)
        h.set_header("sec-ch-ua-mobile", "?0")
        h.set_header("sec-ch-ua-platform", auth.sec_ch_ua_platform)
        h.set_header("sec-fetch-dest", "empty")
        h.set_header("sec-fetch-mode", "cors")
        h.set_header("sec-fetch-site", sec_fetch_site)
        h.set_header("user-agent", auth.user_agent)
        if header_type == HeaderType.POST:
            h.set_header("content-type", "application/json")
        elif header_type == HeaderType.FORM:
            h.set_header("content-type", "application/x-www-form-urlencoded; charset=UTF-8")
        if origin:
            h.set_header("origin", origin)
        h.set_header("cookie", auth.cookie_str)
        return h
