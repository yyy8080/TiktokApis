"""Preview Douyin Creator publish from a local session profile.

Default is a local preflight. Pass ``--publish`` to actually upload.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from api.douyin_web import DouyinWebAPI
from builder.douyin_auth import DouyinAuth, DouyinEvidenceError


def load_auth(profile_path: Path) -> DouyinAuth:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError("浏览器资料必须是 JSON 对象")
    cookie = os.environ.get("DOUYIN_COOKIE") or profile.get("cookie") or ""
    if not str(cookie).strip():
        raise ValueError("缺少 Cookie：在 profile 的 cookie 或 DOUYIN_COOKIE 中提供")
    auth = DouyinAuth.from_cookie(
        cookie,
        user_agent=profile.get("user_agent") or "",
        document_cookie=profile.get("document_cookie") or "",
        device_id=profile.get("device_id") or "",
        webid=profile.get("webid") or "",
        ticket_guard_private_key=profile.get("ticket_guard_private_key") or "",
        ticket_guard_encrypt_ticket=profile.get("ticket_guard_encrypt_ticket") or "",
        ticket_guard_ts_sign=profile.get("ticket_guard_ts_sign") or "",
    )
    auth.require_session()
    return auth


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="从当前 Douyin 会话发布视频或图集")
    parser.add_argument("--profile", type=Path, default=Path(".douyin-runtime.json"))
    parser.add_argument("--publish", action="store_true")
    sub = parser.add_subparsers(dest="kind", required=True)
    video = sub.add_parser("video")
    video.add_argument("media", type=Path)
    video.add_argument("--text", required=True)
    photos = sub.add_parser("photos")
    photos.add_argument("images", nargs="+", type=Path)
    photos.add_argument("--text", required=True)
    args = parser.parse_args(argv)
    try:
        auth = load_auth(args.profile)
        paths = [args.media] if args.kind == "video" else args.images
        for path in paths:
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"媒体文件不存在或为空: {path}")
    except (OSError, ValueError, DouyinEvidenceError) as exc:
        print(f"本地预检失败：{exc}", file=sys.stderr)
        return 2
    if not args.publish:
        print(f"本地预检通过：{args.kind}，{len(paths)} 个文件，默认仅自己可见。")
        return 0
    api = DouyinWebAPI(auth)
    try:
        if args.kind == "video":
            result = api.creator_publish(str(paths[0]), args.text)
        else:
            result = api.creator_publish_photos([str(p) for p in paths], args.text)
    except Exception:
        print("发布未完成。媒体可能已部分上传。", file=sys.stderr)
        return 1
    print(json.dumps({"status_code": (result or {}).get("status_code")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
