import asyncio
import websockets
import time

async def test():
    header = {
        'Upgrade': 'websocket',
        'Sec-Webscoket-Extensions': 'permessage-deflate; client_max_window_bits',
        'Host': 'api-v2.blaze.com',
        'Origin': 'https://blaze.com',
        'Sec-Webscoket-Key': 'wrvXWYFEBzj9IiVmeJ/qxQ==',
        'Sec-Webscoket-Version': '13',
        'Pragma': 'no-cache',
        'Connection': 'Upgrade',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    }

    while True:
        try:
            async with websockets.connect('wss://api-v2.blaze.com/replication/?EIO=3&transport=websocket', extra_headers=header, max_size=2**25) as websocket:
                # Envia o comando de subscribe
                await websocket.send('423["cmd",{"id":"subscribe","payload":{"room":"double_v2"}}]')

                async for message in websocket:
                    print(message)
        except websockets.exceptions.ConnectionClosedError:
            print("Connection lost. Reconnecting...")
            time.sleep(5)  # wait for 5 seconds before trying to reconnect
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

asyncio.get_event_loop().run_until_complete(test())
