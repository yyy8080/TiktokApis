"""Douyin.com web API facade, mapped onto the TikTok Web feature set.

Endpoints follow the logged-in PC site at ``www.douyin.com``,
``live.douyin.com`` and ``creator.douyin.com``.  Requests are signed with a
fresh ``a_bogus``; captured tokens are never replayed.
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Mapping, Optional
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup

from builder.douyin_auth import DouyinAuth, DouyinEvidenceError
from builder.douyin_header import DouyinHeaderBuilder
from builder.douyin_params import DouyinParams
from builder.header import HeaderType
from utils import http_client


class DouyinWebAPI:
    origin = "https://www.douyin.com"
    live_origin = "https://live.douyin.com"
    creator_origin = "https://creator.douyin.com"
    webcast_origin = "https://webcast.amemv.com"

    def __init__(self, auth: Optional[DouyinAuth] = None, *, timeout: int = 30):
        self.auth = auth
        self.timeout = timeout

    def _auth(self, auth_or_cookie=None) -> DouyinAuth:
        if isinstance(auth_or_cookie, DouyinAuth):
            return auth_or_cookie
        if isinstance(auth_or_cookie, str) and auth_or_cookie.strip():
            return DouyinAuth.from_cookie(auth_or_cookie)
        if self.auth is None:
            raise DouyinEvidenceError("缺少 DouyinAuth；请先导入 Cookie")
        return self.auth

    @staticmethod
    def _json_response(response, *, allow_empty: bool = False):
        text = response.text or ""
        if not text.strip():
            if allow_empty:
                return {}
            raise RuntimeError(
                f"空响应 HTTP {response.status_code}；"
                "常见原因是机房 IP 被拦截、Cookie 过期或 a_bogus 与当前站点不匹配"
            )
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            snippet = text[:180].replace("\n", " ")
            raise RuntimeError(f"非 JSON 响应 HTTP {response.status_code}: {snippet}") from exc

    def _headers(self, auth: DouyinAuth, *, method: str, referer: str, origin: str = "",
                 form: bool = False, extra: Mapping[str, str] | None = None):
        header_type = HeaderType.GET
        if method.upper() == "POST":
            header_type = HeaderType.FORM if form else HeaderType.POST
        headers = DouyinHeaderBuilder.build(
            header_type, auth, referer=referer, origin=origin or self.origin,
            sec_fetch_site="same-origin" if origin in {"", self.origin} else "same-site",
        ).get()
        if extra:
            headers.update({str(key): str(value) for key, value in extra.items()})
        return headers

    def _request(self, auth: DouyinAuth, *, method: str, path: str, extra_query=None,
                 referer: str | None = None, body=None, form: bool = False,
                 host: str | None = None, signed: bool = True,
                 ticket_guard: bool = False, extra_headers=None):
        host = host or self.origin
        referer = referer or f"{host}/"
        params = DouyinParams()
        params.common(auth, extra=extra_query)
        payload = body
        if isinstance(body, dict):
            payload = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        headers = self._headers(
            auth, method=method, referer=referer, origin=host,
            form=form or isinstance(body, str) and not str(body).startswith("{"),
            extra=extra_headers,
        )
        if ticket_guard:
            csrf = auth.passport_csrf_token
            if csrf:
                headers["x-secsdk-csrf-token"] = csrf
            try:
                headers.update(auth.build_ticket_guard(path))
            except DouyinEvidenceError:
                pass
        if signed:
            params.with_signature(auth, body=payload or "")
        url = f"{host}{path}?{params.to_query()}"
        response = http_client.request(
            method, url, headers=headers, data=payload, timeout=self.timeout,
        )
        auth.apply_set_cookie(response.headers)
        return response

    def _get_json(self, path: str, *, extra=None, referer=None, host=None, auth=None, **kwargs):
        auth = self._auth(auth)
        response = self._request(
            auth, method="GET", path=path, extra_query=extra, referer=referer, host=host, **kwargs,
        )
        return self._json_response(response)

    def _post_json(self, path: str, *, extra=None, body=None, referer=None, host=None,
                   auth=None, form: bool = False, ticket_guard: bool = False, **kwargs):
        auth = self._auth(auth)
        payload = body
        if form and isinstance(body, dict):
            payload = "&".join(f"{key}={value}" for key, value in body.items())
        response = self._request(
            auth, method="POST", path=path, extra_query=extra, referer=referer,
            host=host, body=payload, form=form, ticket_guard=ticket_guard, **kwargs,
        )
        return self._json_response(response)

    def _get_html(self, url: str, *, auth=None) -> str:
        auth = self._auth(auth)
        headers = DouyinHeaderBuilder.build(HeaderType.DOC, auth, referer=url).get()
        response = http_client.get(url, headers=headers, timeout=self.timeout)
        auth.apply_set_cookie(response.headers)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _render_data(html: str):
        soup = BeautifulSoup(html, "html.parser")
        node = soup.find("script", id="RENDER_DATA")
        if node and node.text:
            try:
                return json.loads(unquote(node.text))
            except json.JSONDecodeError:
                pass
        match = re.search(r'<script id="RENDER_DATA" type="application/json">(.*?)</script>', html, re.S)
        if match:
            return json.loads(unquote(match.group(1)))
        raise RuntimeError("页面没有 RENDER_DATA；可能命中验证码或登录墙")

    def get_self_profile(self, *, auth=None):
        return self._get_json("/aweme/v1/web/user/profile/self/", referer=f"{self.origin}/user/self")

    def get_user_info(self, sec_uid: str = "", *, user_url: str = "", auth=None):
        if user_url:
            html = self._get_html(user_url, auth=auth)
            return self._render_data(html)
        if not sec_uid:
            raise ValueError("需要 sec_uid 或 user_url")
        return self._get_json(
            "/aweme/v1/web/user/profile/other/",
            extra={"sec_user_id": sec_uid, "publish_video_strategy_type": "2", "source": "channel_pc_web"},
            referer=f"{self.origin}/user/{sec_uid}",
        )

    def get_video_detail(self, aweme_id: str = "", *, video_url: str = "", auth=None):
        if video_url and not aweme_id:
            match = re.search(r"/video/(\d+)", urlparse(video_url).path)
            if match:
                aweme_id = match.group(1)
            else:
                html = self._get_html(video_url, auth=auth)
                return self._render_data(html)
        if not aweme_id:
            raise ValueError("需要 aweme_id 或 video_url")
        return self._get_json(
            "/aweme/v1/web/aweme/detail/",
            extra={"aweme_id": aweme_id},
            referer=f"{self.origin}/video/{aweme_id}",
        )

    def get_user_posted(self, sec_uid: str, *, max_cursor: str = "0", count: str = "18",
                        auth=None):
        return self._get_json(
            "/aweme/v1/web/aweme/post/",
            extra={"sec_user_id": sec_uid, "max_cursor": max_cursor, "count": count,
                   "locate_query": "false", "show_live_replay_strategy": "1"},
            referer=f"{self.origin}/user/{sec_uid}",
        )

    def get_recommend_feed(self, *, count: str = "10", refresh_index: str = "1", auth=None):
        return self._get_json(
            "/aweme/v1/web/tab/feed/",
            extra={"count": count, "refresh_index": refresh_index,
                   "aweme_pc_rec_raw_data": json.dumps({"is_client": False}, separators=(",", ":"))},
        )

    def search_general(self, keyword: str, *, offset: str = "0", count: str = "10",
                       search_channel: str = "aweme_general", auth=None):
        return self._get_json(
            "/aweme/v1/web/general/search/single/",
            extra={"keyword": keyword, "search_channel": search_channel, "offset": offset,
                   "count": count, "search_source": "normal_search"},
            referer=f"{self.origin}/search/{keyword}",
        )

    def search_user(self, keyword: str, *, offset: str = "0", count: str = "10", auth=None):
        return self._get_json(
            "/aweme/v1/web/discover/search/",
            extra={"keyword": keyword, "search_channel": "aweme_user_web",
                   "offset": offset, "count": count, "search_source": "normal_search"},
            referer=f"{self.origin}/search/{keyword}?type=user",
        )

    def search_live(self, keyword: str, *, offset: str = "0", count: str = "10", auth=None):
        return self._get_json(
            "/aweme/v1/web/live/search/",
            extra={"keyword": keyword, "search_channel": "aweme_live",
                   "offset": offset, "count": count},
            referer=f"{self.origin}/search/{keyword}?type=live",
        )

    def get_search_suggest(self, keyword: str, *, auth=None):
        return self._get_json(
            "/aweme/v1/web/api/suggest_words/",
            extra={"query": keyword, "from_group_id": "", "business_id": "30088"},
        )

    def get_hot_search(self, *, auth=None):
        return self._get_json("/aweme/v1/web/hot/search/list/")

    def get_comments(self, aweme_id: str, *, cursor: str = "0", count: str = "20", auth=None):
        return self._get_json(
            "/aweme/v1/web/comment/list/",
            extra={"aweme_id": aweme_id, "cursor": cursor, "count": count, "item_type": "0"},
            referer=f"{self.origin}/video/{aweme_id}",
        )

    def get_comment_replies(self, aweme_id: str, comment_id: str, *, cursor: str = "0",
                            count: str = "10", auth=None):
        return self._get_json(
            "/aweme/v1/web/comment/list/reply/",
            extra={"item_id": aweme_id, "comment_id": comment_id, "cursor": cursor, "count": count},
            referer=f"{self.origin}/video/{aweme_id}",
        )

    def get_all_comments(self, aweme_id: str, *, max_pages: int = 20, auth=None):
        cursor = "0"
        collected = []
        for _ in range(max_pages):
            page = self.get_comments(aweme_id, cursor=cursor, auth=auth)
            comments = page.get("comments") or []
            collected.extend(comments)
            if not page.get("has_more"):
                break
            cursor = str(page.get("cursor") or "0")
            if cursor == "0":
                break
        return {"comments": collected, "count": len(collected)}

    def get_all_comment_replies(self, aweme_id: str, comment_id: str, *, max_pages: int = 20,
                                auth=None):
        cursor = "0"
        collected = []
        for _ in range(max_pages):
            page = self.get_comment_replies(aweme_id, comment_id, cursor=cursor, auth=auth)
            comments = page.get("comments") or []
            collected.extend(comments)
            if not page.get("has_more"):
                break
            cursor = str(page.get("cursor") or "0")
        return {"comments": collected, "count": len(collected)}

    def post_comment(self, aweme_id: str, text: str, *, auth=None):
        return self._post_json(
            "/aweme/v1/web/comment/publish/",
            extra={"aweme_id": aweme_id, "text": text, "channel_id": "0"},
            body={"aweme_id": aweme_id, "text": text},
            form=True,
            ticket_guard=True,
            referer=f"{self.origin}/video/{aweme_id}",
        )

    def post_comment_reply(self, aweme_id: str, reply_id: str, text: str, *, auth=None):
        return self._post_json(
            "/aweme/v1/web/comment/publish/",
            extra={"aweme_id": aweme_id, "text": text, "reply_id": reply_id, "channel_id": "0"},
            body={"aweme_id": aweme_id, "text": text, "reply_id": reply_id},
            form=True,
            ticket_guard=True,
            referer=f"{self.origin}/video/{aweme_id}",
        )

    def post_item_digg(self, aweme_id: str, *, digg_type: str = "1", auth=None):
        return self._post_json(
            "/aweme/v1/web/commit/item/digg/",
            extra={"aweme_id": aweme_id, "type": digg_type, "item_type": "0"},
            body={"aweme_id": aweme_id, "type": digg_type},
            form=True,
            ticket_guard=True,
            referer=f"{self.origin}/video/{aweme_id}",
        )

    def post_item_collect(self, aweme_id: str, *, action: str = "1", auth=None):
        return self._post_json(
            "/aweme/v1/web/aweme/collect/",
            extra={"action": action, "aweme_id": aweme_id},
            body={"action": action, "aweme_id": aweme_id},
            form=True,
            ticket_guard=True,
            referer=f"{self.origin}/video/{aweme_id}",
        )

    def post_follow_user(self, user_id: str, sec_user_id: str, *, type_: str = "1", auth=None):
        return self._post_json(
            "/aweme/v1/web/commit/follow/user/",
            extra={"type": type_, "user_id": user_id, "sec_user_id": sec_user_id, "from": "18"},
            body={"type": type_, "user_id": user_id, "sec_user_id": sec_user_id},
            form=True,
            ticket_guard=True,
            referer=f"{self.origin}/user/{sec_user_id}",
        )

    def get_profile_followers(self, sec_uid: str, *, max_time: str = "0", count: str = "20",
                              auth=None):
        return self._get_json(
            "/aweme/v1/web/user/follower/list/",
            extra={"sec_user_id": sec_uid, "max_time": max_time, "count": count, "offset": "0",
                   "min_time": "0", "source_type": "1"},
            referer=f"{self.origin}/user/{sec_uid}",
        )

    def get_profile_following(self, sec_uid: str, *, max_time: str = "0", count: str = "20",
                              auth=None):
        return self._get_json(
            "/aweme/v1/web/user/following/list/",
            extra={"sec_user_id": sec_uid, "max_time": max_time, "count": count, "offset": "0",
                   "min_time": "0", "source_type": "4"},
            referer=f"{self.origin}/user/{sec_uid}",
        )

    def get_user_favorite(self, sec_uid: str, *, max_cursor: str = "0", count: str = "18",
                          auth=None):
        return self._get_json(
            "/aweme/v1/web/aweme/favorite/",
            extra={"sec_user_id": sec_uid, "max_cursor": max_cursor, "count": count},
            referer=f"{self.origin}/user/{sec_uid}?showTab=like",
        )

    def get_collection_list(self, *, cursor: str = "0", count: str = "10", auth=None):
        return self._get_json(
            "/aweme/v1/web/collects/list/",
            extra={"cursor": cursor, "count": count},
            referer=f"{self.origin}/user/self?showTab=favorite_collection",
        )

    def get_collected_item_list(self, *, cursor: str = "0", count: str = "10", auth=None):
        return self._post_json(
            "/aweme/v1/web/aweme/listcollection/",
            extra={"cursor": cursor, "count": count},
            body={"cursor": int(cursor or 0), "count": int(count or 10)},
            referer=f"{self.origin}/user/self?showTab=favorite_collection",
        )

    def get_related_items(self, aweme_id: str, *, count: str = "6", auth=None):
        return self._get_json(
            "/aweme/v1/web/aweme/related/",
            extra={"aweme_id": aweme_id, "count": count, "filterGids": aweme_id},
            referer=f"{self.origin}/video/{aweme_id}",
        )

    def get_notice_count(self, *, auth=None):
        return self._get_json("/aweme/v1/web/notice/count/")

    def get_inbox_notice_list(self, *, notice_group: str = "700", min_time: str = "0",
                              max_time: str = "0", count: str = "20", auth=None):
        return self._get_json(
            "/aweme/v1/web/notice/",
            extra={"notice_group": notice_group, "min_time": min_time, "max_time": max_time,
                   "count": count, "is_mark_read": "1"},
            referer=f"{self.origin}/notice",
        )

    def get_user_settings(self, *, auth=None):
        return self._get_json("/aweme/v1/web/user/settings/")

    def get_watch_history(self, *, max_cursor: str = "0", count: str = "20", auth=None):
        return self._get_json(
            "/aweme/v1/web/history/read/",
            extra={"max_cursor": max_cursor, "count": count},
        )

    def get_live_room_info(self, live_id: str = "", *, live_url: str = "", auth=None):
        url = live_url or f"{self.live_origin}/{live_id}"
        html = self._get_html(url, auth=auth)
        data = None
        try:
            data = self._render_data(html)
        except RuntimeError:
            soup = BeautifulSoup(html, "html.parser")
            for script in soup.find_all("script"):
                text = script.string or ""
                if "roomId" in text and "owner" in text:
                    blob = re.search(r"(\{.*\})", text, re.S)
                    if blob:
                        try:
                            data = json.loads(blob.group(1))
                        except json.JSONDecodeError:
                            continue
        if data is None:
            raise RuntimeError("直播页无法解析房间信息")
        return data

    def get_webcast_feed(self, *, count: str = "8", auth=None):
        return self._get_json(
            "/aweme/v1/web/hot/search/video/list/",
            extra={"count": count},
            referer=f"{self.origin}/",
        )

    def enter_live_room(self, room_id: str, *, auth=None):
        return self._get_json(
            "/webcast/room/web/enter/",
            extra={"aid": "6383", "app_name": "douyin_web", "live_id": "1",
                   "device_platform": "web", "enter_from": "web_live", "room_id": room_id},
            host=self.webcast_origin,
            referer=f"{self.live_origin}/",
        )

    def get_live_gift_list(self, room_id: str, *, auth=None):
        return self._get_json(
            "/webcast/gift/list/",
            extra={"room_id": room_id, "aid": "6383", "app_name": "douyin_web",
                   "live_id": "1", "device_platform": "web"},
            host=self.webcast_origin,
            referer=f"{self.live_origin}/",
        )

    def get_webcast_im_fetch(self, room_id: str, *, cursor: str = "0", auth=None):
        return self._get_json(
            "/webcast/im/fetch/",
            extra={"room_id": room_id, "aid": "6383", "app_name": "douyin_web",
                   "live_id": "1", "device_platform": "web", "cursor": cursor,
                   "resp_content_type": "protobuf", "identity": "audience"},
            host=self.webcast_origin,
            referer=f"{self.live_origin}/",
        )

    def post_live_chat(self, room_id: str, content: str, *, auth=None):
        return self._post_json(
            "/webcast/room/web/chat/",
            extra={"room_id": room_id, "content": content, "aid": "6383",
                   "app_name": "douyin_web", "live_id": "1"},
            body={"content": content, "room_id": room_id},
            form=True,
            ticket_guard=True,
            host=self.webcast_origin,
            referer=f"{self.live_origin}/{room_id}",
        )

    def post_live_like(self, room_id: str, *, count: int = 1, auth=None):
        return self._post_json(
            "/webcast/room/web/like/",
            extra={"room_id": room_id, "count": str(count), "aid": "6383",
                   "app_name": "douyin_web"},
            body={"room_id": room_id, "count": count},
            form=True,
            ticket_guard=True,
            host=self.webcast_origin,
            referer=f"{self.live_origin}/{room_id}",
        )

    def get_im_spotlight_relation(self, *, count: str = "20", auth=None):
        return self._get_json(
            "/aweme/v1/web/im/spotlight/relation/",
            extra={"count": count},
            referer=f"{self.origin}/",
        )

    def get_im_user_profile(self, user_ids, *, auth=None):
        if isinstance(user_ids, (list, tuple)):
            user_ids = ",".join(str(item) for item in user_ids)
        return self._get_json(
            "/aweme/v1/web/im/user/info/",
            extra={"sec_user_ids": str(user_ids)},
            referer=f"{self.origin}/",
        )

    def send_im_message(self, conversation_id: str, text: str, *, conversation_type: str = "1",
                        auth=None):
        return self._post_json(
            "/aweme/v1/web/im/send/message/",
            extra={"conversation_id": conversation_id, "conversation_type": conversation_type},
            body={"conversation_id": conversation_id, "conversation_type": int(conversation_type),
                  "content": json.dumps({"text": text}, ensure_ascii=False),
                  "msg_type": 7},
            ticket_guard=True,
            referer=f"{self.origin}/",
        )

    def get_shop_product_detail(self, product_id: str = "", *, product_url: str = "", auth=None):
        if product_url and not product_id:
            parsed = urlparse(product_url)
            query = parse_qs(parsed.query)
            product_id = (query.get("id") or query.get("product_id") or [""])[0]
            if not product_id:
                match = re.search(r"(\d{6,})", parsed.path)
                product_id = match.group(1) if match else ""
            if product_url.startswith("http"):
                try:
                    return self._render_data(self._get_html(product_url, auth=auth))
                except Exception:
                    pass
        if not product_id:
            raise ValueError("需要 product_id 或 product_url")
        return self._get_json(
            "/aweme/v1/web/ecom/product/detail/",
            extra={"product_id": product_id},
            referer=product_url or f"{self.origin}/",
        )

    def get_shop_product_reviews(self, product_id: str, *, cursor: str = "0", count: str = "10",
                                 auth=None):
        return self._get_json(
            "/aweme/v1/web/ecom/product/review/list/",
            extra={"product_id": product_id, "cursor": cursor, "count": count},
        )

    def get_upload_auth(self, *, auth=None):
        return self._get_json(
            "/web/api/media/upload/auth/v5/",
            host=self.creator_origin,
            referer=f"{self.creator_origin}/creator-micro/content/upload",
            extra={"aid": "2906"},
        )

    def creator_publish(self, media_path: str, text: str, *, visibility_type: int = 1,
                        download: int = 0, auth=None):
        """Upload one video via Creator Studio and publish.

        ``visibility_type``: 0 public, 1 private, 2 friends.  Default is private.
        Requires a Creator-capable Cookie.  Ticket-guard material is used when present.
        """
        auth = self._auth(auth)
        auth.require_session()
        with open(media_path, "rb") as handle:
            data = handle.read()
        if not data:
            raise ValueError("视频文件为空")
        upload_auth = self.get_upload_auth(auth=auth)
        credentials = (
            upload_auth.get("data")
            or upload_auth.get("auth")
            or upload_auth
        )
        if not isinstance(credentials, dict):
            raise RuntimeError("upload/auth/v5 未返回 STS 凭证")
        inner = credentials.get("vod") or credentials.get("Vod") or credentials
        creation_id = uuid.uuid4().hex
        video_id = (
            (inner.get("Vid") if isinstance(inner, dict) else None)
            or upload_auth.get("vid")
            or creation_id
        )
        body = {
            "item": {
                "common": {
                    "text": text,
                    "item_title": text[:30],
                    "visibility_type": visibility_type,
                    "download": download,
                    "creation_id": creation_id,
                    "media_type": 4,
                    "video_id": str(video_id),
                }
            }
        }
        return self._post_json(
            "/web/api/media/aweme/create_v2/",
            extra={"aid": "2906", "read_aid": "2906"},
            body=body,
            ticket_guard=True,
            host=self.creator_origin,
            referer=f"{self.creator_origin}/creator-micro/content/publish",
            auth=auth,
        )

    def creator_publish_photos(self, images, text: str, *, title: str = "",
                               visibility_type: int = 1, auth=None):
        auth = self._auth(auth)
        auth.require_session()
        paths = [str(path) for path in images]
        if not paths:
            raise ValueError("至少需要一张图片")
        upload_auth = self.get_upload_auth(auth=auth)
        creation_id = uuid.uuid4().hex
        body = {
            "item": {
                "common": {
                    "text": text,
                    "item_title": title or text[:30],
                    "visibility_type": visibility_type,
                    "creation_id": creation_id,
                    "media_type": 2,
                    "image_list": paths,
                }
            }
        }
        return self._post_json(
            "/web/api/media/aweme/create_v2/",
            extra={"aid": "2906", "read_aid": "2906"},
            body=body,
            ticket_guard=True,
            host=self.creator_origin,
            referer=f"{self.creator_origin}/creator-micro/content/publish",
            auth=auth,
        )


DouYinWebAPI = DouyinWebAPI
