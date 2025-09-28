"""Small API-friendly helpers to use Instaloader programmatically from web services.

This module intentionally does not change the existing library logic. Instead it
provides convenience functions that configure an :class:`Instaloader` instance
for embedding into web APIs (quiet logging, no sleeps) and helpers that return
pure Python objects (dicts, bytes) instead of writing files to disk.

Examples
--------
    from instaloader.api import make_loader, get_profile_json, get_post_json, get_post_media

    L = make_loader()
    profile = get_profile_json(L, 'instagram')
    post = get_post_json(L, 'Bxxxxx')
    media = get_post_media(L, 'Bxxxxx')  # list of {"filename", "content", "mime"}
    L.close()
"""
from typing import Dict, List, Optional, Tuple

from .instaloader import Instaloader
from .structures import Profile, Post, StoryItem, TitlePic


def get_stories_for_user(loader: Instaloader, username: str):
    """Return a list of story item dicts for a given username.

    Requires a logged-in session (Instaloader.context.is_logged_in == True).
    Each returned item is a dict with keys: 'mediaid', 'shortcode', 'is_video', 'url', 'date', 'get_bytes'.
    """
    # Ensure profile exists
    profile = Profile.from_username(loader.context, username)
    # Instaloader.get_stories yields Story objects; we want stories of that user
    # Use Instaloader.get_stories with userids=[profile.userid]
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
    """Return (content, mime) tuple for the story media at 1-based `index` of `username`'s current stories."""
    items = get_stories_for_user(loader, username)
    if index < 1 or index > len(items):
        raise IndexError('story index out of range')
    return items[index - 1]['get_bytes']()


def make_loader(sleep: bool = False, quiet: bool = True, sanitize_paths: bool = True) -> Instaloader:
    """Create a pre-configured :class:`Instaloader` instance for use in server APIs.

    Default configuration disables sleeping between requests and enables quiet
    mode so the library doesn't write to stdout/stderr during normal operation.
    """
    return Instaloader(sleep=sleep, quiet=quiet, sanitize_paths=sanitize_paths)


def get_profile_json(loader: Instaloader, username: str) -> Dict:
    """Return a JSON-serializable dict with profile metadata for `username`.

    Raises :class:`instaloader.exceptions.ProfileNotExistsException` if profile
    does not exist or other Instaloader exceptions on failure.
    """
    profile = Profile.from_username(loader.context, username)
    # _asdict returns a plain dict representation of the profile
    return profile._asdict()


def get_post_json(loader: Instaloader, shortcode: str) -> Dict:
    """Return a JSON-serializable dict with post metadata for `shortcode`.

    The function fetches full metadata for the post (this performs network
    requests if required).
    """
    post = Post.from_shortcode(loader.context, shortcode)
    # Accessing _full_metadata forces metadata retrieval; then return dict
    _ = post._full_metadata
    return post._asdict()


def get_profile_picture(loader: Instaloader, username: str) -> Tuple[bytes, str]:
    """Return (content_bytes, mime) of a profile's picture.

    The returned `mime` is an approximation derived from URL extension.
    """
    profile = Profile.from_username(loader.context, username)
    url = profile.profile_pic_url
    resp = loader.context.get_raw(url)
    # try to infer mime from Content-Type header
    mime = resp.headers.get('Content-Type', 'application/octet-stream')
    # read content (requests Response supports .content)
    content = resp.content
    return content, mime


def get_post_media(loader: Instaloader, shortcode: str) -> List[Dict]:
    """Return list of media items for a Post.

    Each item is a dict with keys: 'is_video' (bool), 'url' (str), 'filename' (suggested),
    and a callable 'get_bytes' which when called returns a (bytes, mime) tuple.

    Note: we return a small helper (callable) instead of eagerly downloading all
    media bytes. This is more suitable for web APIs where the caller decides to
    stream or download the bytes.
    """
    post = Post.from_shortcode(loader.context, shortcode)
    # Ensure metadata available
    _ = post._full_metadata

    media_items = []
    # For sidecar posts, iterate sidecar nodes
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
        # single media post
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
