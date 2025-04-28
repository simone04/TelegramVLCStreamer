from typing import Any, Callable, Coroutine, Optional
from telethon.tl.patched import Message
from telethon import TelegramClient

MessageSearchFunction = Callable[
    [TelegramClient],
    Coroutine[Any, Any, Optional[Message]]
]


class Config:
    def __init__(self, api_id : int, api_hash : str, callback : MessageSearchFunction ):
        self.api_id : int = api_id 
        self.api_hash : str = api_hash
        self.callback : MessageSearchFunction = callback
