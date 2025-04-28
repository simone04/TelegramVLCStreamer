import re
from typing import Any, Coroutine 
from aiohttp import web
from telethon import TelegramClient 
from telethon.tl.patched import Message
import subprocess
from user import config 

# Parametri configurabili
CHUNK_SIZE = 1024 * 1024  # 1MB per chunk
DEFAULT_PORT = 8080
VIDEO_CACHE_TIME = 3600  # 1 ora per caching headers
PLAYER_COMMAND = ['vlc', '--network-caching=1000', '--no-metadata-network-access']

async def start_stream_server(client: TelegramClient, message: Message, port=DEFAULT_PORT):
    app = web.Application()
    routes = web.RouteTableDef()

    @routes.get('/stream')
    async def video_stream(request):
        total_size = message.document.size
        range_header = request.headers.get('Range', '')
        headers = {
            'Accept-Ranges': 'bytes',
            'Content-Disposition': 'inline',
            'Cache-Control': f'max-age={VIDEO_CACHE_TIME}, public'
        }

        # Determinazione Content-Type
        mime_type = getattr(message.document, 'mime_type', 'video/mp4')
        headers['Content-Type'] = mime_type or 'video/mp4'

        # Parsing range header
        start, end = 0, total_size - 1
        if range_header:
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else total_size - 1
                end = min(end, total_size - 1)
                
                if start >= total_size: return web.Response(status=416)

                headers['Content-Range'] = f'bytes {start}-{end}/{total_size}'
                status_code = 206
                content_length = end - start + 1

            else: return web.Response(status=416)
        else:
            status_code = 200
            content_length = total_size

        headers['Content-Length'] = str(content_length)
        response = web.StreamResponse( status=status_code, headers=headers)
        await response.prepare(request)

        bytes_remaining = content_length
        async for chunk in client.iter_download( message.document, offset=start, request_size=CHUNK_SIZE, limit=content_length, chunk_size=CHUNK_SIZE):
            if bytes_remaining <= 0: break
            
            chunk_size = min(len(chunk), bytes_remaining)
            await response.write(chunk[:chunk_size])
            bytes_remaining -= chunk_size

        return response

    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Server streaming running: http://localhost:{port}/stream")
    return site, runner

async def stream(client: TelegramClient, message_callback: Coroutine[Any, Any, Message | None]):
    await client.start()
    message = await message_callback

    stream_server, runner = await start_stream_server(client, message)
    
    try:
        subprocess.Popen([*PLAYER_COMMAND, f'http://localhost:{DEFAULT_PORT}/stream'])
        await client.run_until_disconnected()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    client = TelegramClient('session', config.api_id, config.api_hash)
    with client:
        message_promise = config.callback(client)
        client.loop.run_until_complete(stream(client, message_promise))