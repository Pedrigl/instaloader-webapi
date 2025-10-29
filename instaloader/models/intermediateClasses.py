from dataclasses import dataclass
import json
from typing import List
@dataclass
class FetchedStoryItem:

    def __init__(self, mediaid: int, shortcode: str, is_video: bool, url: str, date: str):
        self.mediaid = mediaid
        self.shortcode = shortcode
        self.is_video = is_video
        self.url = url
        self.date = date

    mediaid: int
    shortcode: str
    is_video: bool
    url: str
    date: str
