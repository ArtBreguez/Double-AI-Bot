import asyncio
import websockets
import time
import re

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
                            match = re.search(r'"status":"waiting"', message)
                            if match:
                                
                            # Procura pelas strings 'total_red_eur_bet' e 'total_black_eur_bet' na mensagem usando regex
                                match = re.search(r'total_red_eur_bet":(\d+\.\d+).*total_black_eur_bet":(\d+\.\d+)', message)
                                if match:
                                    # Se encontrou, extrai os valores e imprime
                                    total_red_eur_bet = match.group(1)
                                    total_black_eur_bet = match.group(2)
                                    print(f"Total red EUR bet: {total_red_eur_bet}, Total black EUR bet: {total_black_eur_bet}")
        except websockets.exceptions.ConnectionClosedError:
            print("Connection lost. Reconnecting...")
            time.sleep(5)  # wait for 5 seconds before trying to reconnect
        except Exception as e:
            print(f"Unexpected error: {e}")
            break


asyncio.get_event_loop().run_until_complete(test())
