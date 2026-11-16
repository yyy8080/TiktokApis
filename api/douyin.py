"""Public Douyin entry that mirrors ``TiktokAPI``."""

from .douyin_web import DouyinWebAPI, DouYinWebAPI

__all__ = ["DouyinAPI", "DouyinWebAPI", "DouYinWebAPI"]


class DouyinAPI(DouyinWebAPI):
    """Cookie-string compatible wrapper, matching ``TiktokAPI``."""

    def get_user_posted(self, secUid, cursor="0", cookies_str=None, **kwargs):
        return super().get_user_posted(secUid, max_cursor=str(cursor), auth=cookies_str, **kwargs)

    def get_video_detail(self, video_url, cookies_str=None, **kwargs):
        return super().get_video_detail(video_url=video_url, auth=cookies_str, **kwargs)

    def get_user_info(self, user_url, cookies_str=None, **kwargs):
        return super().get_user_info(user_url=user_url, auth=cookies_str, **kwargs)

    def get_all_comments(self, aweme_id, cookies_str=None, **kwargs):
        return super().get_all_comments(aweme_id, auth=cookies_str, **kwargs)

    def creator_publish(self, media, text, cookies_str=None, **kwargs):
        return super().creator_publish(media, text, auth=cookies_str, **kwargs)
