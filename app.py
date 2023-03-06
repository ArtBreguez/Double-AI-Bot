import json
import requests
import random
import logging
import urllib
import yaml
import telethon
from telethon import TelegramClient
import asyncio
from telethon.tl.functions.channels import JoinChannelRequest
import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model
import time
import threading
import pickle
from sklearn.preprocessing import LabelEncoder


class Records:
    def __init__(self, id, created_at, color, roll):
        self.id = id
        self.created_at = created_at
        self.color = color
        self.roll = roll

class TotalPages:
    def __init__(self, total_pages, records):
        self.total_pages = total_pages
        self.records = records

game_num = []
game_color = []	
actions = [0, 1, 2, 3]
previous_payload = None
stream = 0

def read_config(file):
    with open(file, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            CHANNEL = config['Channel']
            CHAT_ID = config['ChatID']
            BLAZE = config['Blaze']
            API_HASH = config['API_HASH']
            API_ID = config['API_ID']
            CHANNEL_LINK = config['CHANNEL_LINK']
            MODEL_PATH = config['MODEL_PATH']
            return CHANNEL, CHAT_ID, BLAZE, API_HASH, API_ID, MODEL_PATH, CHANNEL_LINK
        except yaml.YAMLError as e:
            print(e)

CHANNEL, CHAT_ID, BLAZE, API_HASH, API_ID, MODEL_PATH, CHANNEL_LINK = read_config('config.yml')

model = pickle.load(open(MODEL_PATH, 'rb'))
model.epsilon = 0.15
colors = ['red', 'black', 'white', 'white', 'white']
def getBlazeData():
    global previous_payload
    data = requests.get(BLAZE)
    if data.status_code != 200:
        raise Exception("Error getting data from blaze.com")
    result = TotalPages(0, [])
    result = json.loads(data.text)
    payload = json.dumps(result["records"][:20])
    if payload == previous_payload:
        return None
    previous_payload = payload
    game_color = []
    colors = ["red", "black", "white"]
    encoder = LabelEncoder()
    encoder.fit(colors)
    for i, v in enumerate(result["records"]):
        if i == 9:
            break
        color = v["color"]
        game_color.append(encoder.transform([color])[0])
    game_color.reverse()
    return game_color

def predict(game_color):
    if np.random.rand() <= model.epsilon:
        action = random.choice(colors)
        return action
    action = model.predict([game_color])
    return action[0]

def send_message_to_telegram_channel(text):
    message = ""
    if text == 'black':
        message = "A próxima jogada é ⚫"
    elif text == 'red':
        message = "A próxima jogada é 🔴"
    elif text == 'white':
        message = "A próxima jogada é ⚪"
    elif text == 3:
        return
    elif text is None:
        message = "👨🏼‍💻 Não há novas jogadas 🤖"

    encoded_message = urllib.parse.quote(message)
    url = "https://api.telegram.org/bot" + CHANNEL + "/sendMessage?chat_id=" + CHAT_ID + "&text=" + encoded_message

    try:
        file = open("logs/requests.log", "a")
    except:
        logging.error("Failed to open file logs/requests.log")
        return

    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as e:
        logging.error("Error sending message to telegram channel: " + str(e))
        file.close()
        return

    body = resp.text
    logging.basicConfig(filename="logs/requests.log", level=logging.INFO)
    logging.info(body)
    file.close()

def getMachineGuess():
    data = getBlazeData()
    if data is None:
        return send_message_to_telegram_channel(None)
    return send_message_to_telegram_channel(predict(data))

def startStream(onlywhitelist=False):
    global stream
    while stream:
        data = getBlazeData()
        if data is None:
            time.sleep(3)
            continue
        prediction = predict(data)
        if onlywhitelist and prediction != 0:
            time.sleep(3)
            continue
        send_message_to_telegram_channel(prediction)
        time.sleep(3)
    return

def stopStream():
    global stream
    stream = False
    return

def startStreamInThread(onlywhitelist=False):
    thread = threading.Thread(target=startStream, args=(onlywhitelist,))
    thread.start()
     

async def listenMessages():

    # Caminho para o arquivo com o número de telefone e o código de autenticação
    session_file = 'session_name.session'

    # Inicializa o cliente
    client = TelegramClient(session_file, API_ID, API_HASH)

    # Conecta ao Telegram
    await client.start()

    # Encontra o ID do grupo
    group = await client.get_entity(CHANNEL_LINK)
    if isinstance(group, telethon.tl.types.Channel):
        print('ID do canal:', group.id)
        print('Nome do canal:', group.title)
        await client(JoinChannelRequest(group.id))
        print('Escutando mensagens do canal...')
        while True:
            messages = await client.get_messages(group.id, limit=1)
            message = messages[0]
            global stream
            if message.message.strip().lower() == '/roll':
                getMachineGuess()
            if message.message.strip().lower() == '/start_stream':
                stream = True
                startStreamInThread()
            if message.message.strip().lower() == '/start_stream_whitelist':
                stream = True
                startStreamInThread(True)
            if message.message.strip().lower() == '/stop_stream':
                stopStream()
            await asyncio.sleep(2)
    else:
        print(f'Canal "{CHANNEL_LINK}" não encontrado')
        # Encerra a conexão
        await client.disconnect()

    
async def main():
    await listenMessages()

# Iniciar a execução da função main
asyncio.run(main())
