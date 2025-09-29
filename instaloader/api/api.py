from typing import Dict, List, Optional, Tuple

from ..instaloader import Instaloader
from ..structures import Profile, Post, StoryItem, TitlePic


def get_stories_for_user(loader: Instaloader, username: str):
    profile = Profile.from_username(loader.context, username)
    stories = list(loader.get_stories(userids=[profile.userid]))
    items = []
    for story in stories:
        for item in story.get_items():
            url = item.video_url if item.is_video else item.url

            def make_getter(u: str):
                def _get():
                    resp = loader.context.get_raw(u)
                    return resp.content, resp.headers.get('Content-Type', 'application/octet-stream')
                return _get

            items.append({
                'mediaid': item.mediaid,
                'shortcode': item.shortcode,
                'is_video': item.is_video,
                'url': url,
                'date': item.date_utc.isoformat(),
                'get_bytes': make_getter(url),
            })
    return items


def get_story_media(loader: Instaloader, username: str, index: int = 1):
    items = get_stories_for_user(loader, username)
    if index < 1 or index > len(items):
        raise IndexError('story index out of range')
    return items[index - 1]['get_bytes']()


def make_loader(sleep: bool = False, quiet: bool = True, sanitize_paths: bool = True) -> Instaloader:
    
    return Instaloader(sleep=sleep, quiet=quiet, sanitize_paths=sanitize_paths)


def get_profile_json(loader: Instaloader, username: str) -> Dict:
    
    profile = Profile.from_username(loader.context, username)
    return profile._asdict()


def get_post_json(loader: Instaloader, shortcode: str) -> Dict:
    
    post = Post.from_shortcode(loader.context, shortcode)
    
    _ = post._full_metadata
    return post._asdict()


def get_profile_picture(loader: Instaloader, username: str) -> Tuple[bytes, str]:
    
    profile = Profile.from_username(loader.context, username)
    url = profile.profile_pic_url
    resp = loader.context.get_raw(url)
    
    mime = resp.headers.get('Content-Type', 'application/octet-stream')
    
    content = resp.content
    return content, mime


def get_post_media(loader: Instaloader, shortcode: str) -> List[Dict]:
    
    post = Post.from_shortcode(loader.context, shortcode)
    
    _ = post._full_metadata

    media_items = []
    
    if post.typename == 'GraphSidecar':
        for idx, node in enumerate(post.get_sidecar_nodes()):
            url = node.display_url
            is_video = node.is_video
            suggested_name = f"{shortcode}_{idx + 1}"

            def make_getter(u: str):
                def _get():
                    resp = loader.context.get_raw(u)
                    return resp.content, resp.headers.get('Content-Type', 'application/octet-stream')
                return _get

            media_items.append({
                'is_video': is_video,
                'url': url,
                'filename': suggested_name,
                'get_bytes': make_getter(url),
            })
    else:
    
        is_video = post.is_video
        url = post.video_url if is_video else post.url
        suggested_name = f"{shortcode}_1"

        def _get_single():
            resp = loader.context.get_raw(url)
            return resp.content, resp.headers.get('Content-Type', 'application/octet-stream')

        media_items.append({
            'is_video': is_video,
            'url': url,
            'filename': suggested_name,
            'get_bytes': _get_single,
        })

    return media_items
