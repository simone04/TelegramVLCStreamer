# Telegram Video Streamer

A Python script to stream videos from Telegram directly to VLC using [Telethon](https://docs.telethon.dev/en/stable/).

If you see a lot of errors is completely normal (maybe)

## Features
- Stream Telegram videos to VLC without downloading the entire file first
- Lightweight (if i did everything right, probably not) and asynchronous using Telethon 
- Customizable video selection logic

## Prerequisites
- Python 3.8+
- [Telethon](https://github.com/LonamiWebs/Telethon) (`pip install telethon`)
- VLC media player installed

## Setup

1. **Get Telegram API Credentials**  
   Visit [my.telegram.org](https://my.telegram.org) to obtain:
   - `API_ID`
   - `API_HASH`

2. **Configuration**  
   Create a `user.py` file with your configuration:

   ```python
   from typing import Optional
   from Config import Config
   from telethon.tl.patched import Message
   from telethon import TelegramClient

   # Target chat (username, ID, or phone number)
   CHAT = 'your_target_chat_here'

   async def get_video_message(client: TelegramClient) -> Optional[Message]:
       """Custom function to find the video message you want to stream.
       This example returns the first available video in the chat."""
       async for msg in client.iter_messages(CHAT):
           if msg and msg.video:
               return msg
       return None

   # Your Telegram API credentials
   API_ID = '123456'  # Replace with your API_ID
   API_HASH = 'abcdef123456'  # Replace with your API_HASH

   # Initialize config
   config = Config(API_ID, API_HASH, get_video_function)
   ```

## Usage
Run the script:
```bash
python main.py
```

**First run?** You'll need to:
1. Enter your phone number (with country code) in the terminal
2. Confirm the login via Telegram (app or web)

## Customization
Modify `get_video_message()` in `user.py` to implement your own video selection logic. Examples:
- Search videos by caption
- Get latest video from a specific user
- Filter by video duration/size

## How It Works
1. Uses Telethon's async API to fetch messages
2. Streams video content directly to VLC via HTTP
3. No full downloads - starts playback while buffering

## Troubleshooting
- VLC issues: Ensure VLC is installed and in your PATH

---
