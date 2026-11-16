"""Catalog of Douyin console actions mapped onto DouyinWebAPI."""

from __future__ import annotations

from api.douyin_web import DouyinWebAPI


ACTIONS = [
    {
        "id": "get_self_profile",
        "group": "账号",
        "label": "当前账号资料",
        "fields": [],
        "write": False,
    },
    {
        "id": "get_user_info",
        "group": "内容与用户",
        "label": "用户资料",
        "fields": [
            {"name": "sec_uid", "label": "sec_uid", "placeholder": "MS4wLjABAAAA..."},
            {"name": "user_url", "label": "主页 URL", "placeholder": "https://www.douyin.com/user/..."},
        ],
        "write": False,
    },
    {
        "id": "get_video_detail",
        "group": "内容与用户",
        "label": "作品详情",
        "fields": [
            {"name": "aweme_id", "label": "作品 ID"},
            {"name": "video_url", "label": "作品 URL", "placeholder": "https://www.douyin.com/video/..."},
        ],
        "write": False,
    },
    {
        "id": "get_user_posted",
        "group": "内容与用户",
        "label": "主页作品列表",
        "fields": [
            {"name": "sec_uid", "label": "sec_uid", "required": True},
            {"name": "max_cursor", "label": "max_cursor", "value": "0"},
            {"name": "count", "label": "count", "value": "18"},
        ],
        "write": False,
    },
    {
        "id": "get_recommend_feed",
        "group": "内容与用户",
        "label": "推荐流",
        "fields": [{"name": "count", "label": "count", "value": "10"}],
        "write": False,
    },
    {
        "id": "search_general",
        "group": "内容与用户",
        "label": "综合搜索",
        "fields": [
            {"name": "keyword", "label": "关键词", "required": True},
            {"name": "offset", "label": "offset", "value": "0"},
        ],
        "write": False,
    },
    {
        "id": "search_user",
        "group": "内容与用户",
        "label": "搜索用户",
        "fields": [{"name": "keyword", "label": "关键词", "required": True}],
        "write": False,
    },
    {
        "id": "search_live",
        "group": "内容与用户",
        "label": "搜索直播",
        "fields": [{"name": "keyword", "label": "关键词", "required": True}],
        "write": False,
    },
    {
        "id": "get_search_suggest",
        "group": "内容与用户",
        "label": "搜索联想",
        "fields": [{"name": "keyword", "label": "关键词", "required": True}],
        "write": False,
    },
    {
        "id": "get_hot_search",
        "group": "内容与用户",
        "label": "热搜榜",
        "fields": [],
        "write": False,
    },
    {
        "id": "get_related_items",
        "group": "内容与用户",
        "label": "相关作品",
        "fields": [{"name": "aweme_id", "label": "作品 ID", "required": True}],
        "write": False,
    },
    {
        "id": "get_profile_followers",
        "group": "内容与用户",
        "label": "粉丝列表",
        "fields": [{"name": "sec_uid", "label": "sec_uid", "required": True}],
        "write": False,
    },
    {
        "id": "get_profile_following",
        "group": "内容与用户",
        "label": "关注列表",
        "fields": [{"name": "sec_uid", "label": "sec_uid", "required": True}],
        "write": False,
    },
    {
        "id": "get_user_favorite",
        "group": "内容与用户",
        "label": "喜欢的作品",
        "fields": [{"name": "sec_uid", "label": "sec_uid", "required": True}],
        "write": False,
    },
    {
        "id": "get_collection_list",
        "group": "内容与用户",
        "label": "收藏夹列表",
        "fields": [],
        "write": False,
    },
    {
        "id": "get_collected_item_list",
        "group": "内容与用户",
        "label": "收藏的作品",
        "fields": [],
        "write": False,
    },
    {
        "id": "get_watch_history",
        "group": "内容与用户",
        "label": "观看历史",
        "fields": [],
        "write": False,
    },
    {
        "id": "get_notice_count",
        "group": "内容与用户",
        "label": "通知未读数",
        "fields": [],
        "write": False,
    },
    {
        "id": "get_inbox_notice_list",
        "group": "内容与用户",
        "label": "通知列表",
        "fields": [{"name": "notice_group", "label": "分区", "value": "700"}],
        "write": False,
    },
    {
        "id": "get_comments",
        "group": "评论与互动",
        "label": "评论列表",
        "fields": [
            {"name": "aweme_id", "label": "作品 ID", "required": True},
            {"name": "cursor", "label": "cursor", "value": "0"},
        ],
        "write": False,
    },
    {
        "id": "get_comment_replies",
        "group": "评论与互动",
        "label": "楼中楼",
        "fields": [
            {"name": "aweme_id", "label": "作品 ID", "required": True},
            {"name": "comment_id", "label": "评论 ID", "required": True},
        ],
        "write": False,
    },
    {
        "id": "get_all_comments",
        "group": "评论与互动",
        "label": "拉取全部评论",
        "fields": [{"name": "aweme_id", "label": "作品 ID", "required": True}],
        "write": False,
    },
    {
        "id": "post_comment",
        "group": "评论与互动",
        "label": "发评论",
        "fields": [
            {"name": "aweme_id", "label": "作品 ID", "required": True},
            {"name": "text", "label": "内容", "required": True},
        ],
        "write": True,
    },
    {
        "id": "post_comment_reply",
        "group": "评论与互动",
        "label": "回复评论",
        "fields": [
            {"name": "aweme_id", "label": "作品 ID", "required": True},
            {"name": "reply_id", "label": "评论 ID", "required": True},
            {"name": "text", "label": "内容", "required": True},
        ],
        "write": True,
    },
    {
        "id": "post_item_digg",
        "group": "评论与互动",
        "label": "点赞 / 取消点赞",
        "fields": [
            {"name": "aweme_id", "label": "作品 ID", "required": True},
            {"name": "digg_type", "label": "type（1点赞 0取消）", "value": "1"},
        ],
        "write": True,
    },
    {
        "id": "post_item_collect",
        "group": "评论与互动",
        "label": "收藏 / 取消收藏",
        "fields": [
            {"name": "aweme_id", "label": "作品 ID", "required": True},
            {"name": "action", "label": "action（1收藏 0取消）", "value": "1"},
        ],
        "write": True,
    },
    {
        "id": "post_follow_user",
        "group": "评论与互动",
        "label": "关注 / 取关",
        "fields": [
            {"name": "user_id", "label": "user_id", "required": True},
            {"name": "sec_user_id", "label": "sec_uid", "required": True},
            {"name": "type_", "label": "type（1关注 0取关）", "value": "1"},
        ],
        "write": True,
    },
    {
        "id": "get_live_room_info",
        "group": "直播",
        "label": "直播间信息",
        "fields": [
            {"name": "live_id", "label": "直播间 ID"},
            {"name": "live_url", "label": "直播 URL"},
        ],
        "write": False,
    },
    {
        "id": "enter_live_room",
        "group": "直播",
        "label": "进入直播间",
        "fields": [{"name": "room_id", "label": "room_id", "required": True}],
        "write": False,
    },
    {
        "id": "get_live_gift_list",
        "group": "直播",
        "label": "礼物列表",
        "fields": [{"name": "room_id", "label": "room_id", "required": True}],
        "write": False,
    },
    {
        "id": "get_webcast_im_fetch",
        "group": "直播",
        "label": "直播消息拉取",
        "fields": [{"name": "room_id", "label": "room_id", "required": True}],
        "write": False,
    },
    {
        "id": "post_live_chat",
        "group": "直播",
        "label": "发弹幕",
        "fields": [
            {"name": "room_id", "label": "room_id", "required": True},
            {"name": "content", "label": "内容", "required": True},
        ],
        "write": True,
    },
    {
        "id": "post_live_like",
        "group": "直播",
        "label": "直播点赞",
        "fields": [
            {"name": "room_id", "label": "room_id", "required": True},
            {"name": "count", "label": "次数", "value": "1"},
        ],
        "write": True,
    },
    {
        "id": "get_im_spotlight_relation",
        "group": "私信",
        "label": "私信关系列表",
        "fields": [],
        "write": False,
    },
    {
        "id": "get_im_user_profile",
        "group": "私信",
        "label": "私信用户资料",
        "fields": [{"name": "user_ids", "label": "sec_uid，逗号分隔", "required": True}],
        "write": False,
    },
    {
        "id": "send_im_message",
        "group": "私信",
        "label": "发送文本私信",
        "fields": [
            {"name": "conversation_id", "label": "会话 ID", "required": True},
            {"name": "text", "label": "文本", "required": True},
            {"name": "conversation_type", "label": "类型（1私聊 2群）", "value": "1"},
        ],
        "write": True,
    },
    {
        "id": "get_shop_product_detail",
        "group": "电商",
        "label": "商品详情",
        "fields": [
            {"name": "product_id", "label": "商品 ID"},
            {"name": "product_url", "label": "商品 URL"},
        ],
        "write": False,
    },
    {
        "id": "get_shop_product_reviews",
        "group": "电商",
        "label": "商品评价",
        "fields": [{"name": "product_id", "label": "商品 ID", "required": True}],
        "write": False,
    },
    {
        "id": "get_upload_auth",
        "group": "创作者",
        "label": "上传鉴权",
        "fields": [],
        "write": False,
    },
]


def run_action(api: DouyinWebAPI, action_id: str, payload: dict):
    method = getattr(api, action_id, None)
    if method is None or not callable(method):
        raise ValueError(f"未知操作: {action_id}")
    spec = next((item for item in ACTIONS if item["id"] == action_id), None)
    if spec is None:
        raise ValueError(f"未知操作: {action_id}")
    kwargs = {}
    for field in spec["fields"]:
        name = field["name"]
        if name not in payload:
            continue
        value = payload[name]
        if value is None or value == "":
            continue
        if name == "count" and action_id == "post_live_like":
            kwargs[name] = int(value)
        else:
            kwargs[name] = value
    return method(**kwargs)
