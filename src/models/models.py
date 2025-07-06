from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Post:
    uri: str
    cid: str
    author_did: str
    text: str
    created_at: str
    reply_count: int = 0
    repost_count: int = 0
    like_count: int = 0
    quote_count: int = 0
    embed_images: List[str] = field(default_factory=list)
    replies: List['Post'] = field(default_factory=list)

@dataclass
class BlueSkyUser:
    handle: str
    did: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    profile_picture_url: Optional[str] = None
    banner_url: Optional[str] = None
    posts: List[Post] = field(default_factory=list)