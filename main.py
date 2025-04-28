import re
from typing import Any, Coroutine 
from aiohttp import web
from telethon import TelegramClient 
from telethon.tl.patched import Message
import subprocess
from user import config 


async def start_stream_server(client : TelegramClient, message : Message, port=8080):
    app = web.Application()
    routes = web.RouteTableDef()

    @routes.get('/stream')
    async def video_stream(request):

        chunk_size = 256 * 1024 

        range_header = request.headers.get('Range')
        total_size = message.document.size
        offset = 0

        headers = {
            'Content-Type': 'video/mp4',
            'Content-Disposition': 'inline',
            'Accept-Ranges': 'bytes',
            'Content-Length': None
        }
        status_code = 200 

        limit = total_size

        # from here just a big mess, onestly i lost track of the variables
        if range_header:
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start_str, end_str = match.groups()
                offset = int(start_str)

                if end_str: 
                    limit = int(end_str) - offset + 1

                else: 
                    limit = total_size - offset
                
                if offset + limit > total_size: 
                    limit = total_size - offset
                        
                if offset >= total_size or limit <= 0: 
                    return web.Response(status=416, text="Range Not Satisfiable")

                status_code = 206 # Partial Content
                headers['Content-Range'] = f'bytes {offset}-{offset + limit - 1}/{total_size}'
                headers['Content-Length'] = str(limit)            
            else:
                range_header = None 
                headers['Content-Length'] = str(total_size)
        else:
            headers['Content-Length'] = str(total_size)
        
        response = web.StreamResponse(status=status_code, headers=headers)
        await response.prepare(request)

        bytes_to_send = limit

        async for chunk in client.iter_download(message.document, offset=offset,  request_size=limit,  limit=limit,  chunk_size=chunk_size):
            if not chunk: break
            
            send_now = min(len(chunk), bytes_to_send)

            if send_now <= 0: break

            await response.write(chunk[:send_now])
            bytes_to_send -= send_now
            
            if bytes_to_send <= 0: break
        await response.write_eof()
        return response
    
    app.add_routes(routes)
    app['client'] = client
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', port) 
    await site.start()
    print(f"Stream server ready on http://localhost:{port}") 
    return site, runner


async def stream(client : TelegramClient, message_callback : Coroutine[Any, Any, Message | None]):
    await client.start()
    print("Client started")
    message = await message_promise

    stream_server, runner = await start_stream_server(client, message)

    stream_url = "http://localhost:8080/stream?"
    print(f"Attempting to stream: {stream_url}")
    
    subprocess.Popen(['vlc', '--no-metadata-network-access', stream_url])

    await client.run_until_disconnected()
    await runner.cleanup()




if __name__ == "__main__":
    client = TelegramClient('session', config.api_id, config.api_hash)
    with client:
        message_promise = config.callback(client)
        client.loop.run_until_complete(stream(client, message_promise))