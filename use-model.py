import json
import requests
import os
import random
import ioutil
import logging
import logrus
import urllib
import yaml
import telethon
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
import asyncio
from telethon.tl.functions.channels import JoinChannelRequest
import time
import tensorflow as tf
from tensorflow import keras
import numpy as np
from tensorflow.keras.models import load_model

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

model = load_model(MODEL_PATH)
model.epsilon = 0.3
model.q_network = tf.keras.models.load_model(MODEL_PATH)
model.target_network = tf.keras.models.load_model(MODEL_PATH)

def getBlazeData():
    colors = []
    data = requests.get(BLAZE)
    if data.status_code != 200:
        raise Exception("Error getting data from blaze.com")
    result = TotalPages(0, [])
    result = json.loads(data.text)
    for i, v in enumerate(result["records"]):
        if i == 20:
            break
        num = int(v["roll"])
        color = v["color"]
        if color == "green":
            color = "white"
        colors.append(color)
        game_num.append(num)
        game_color.append(color)
    colors = list(reversed(colors))
    game_num.reverse()
    game_color.reverse()
    return colors

def predict():
    data = getBlazeData()
    if data is None:
        return
    state = []
    for i in range(len(game_num)):
        state = game_num[max(0, i-19):i+1]
        if len(state) < 20:
            continue

        state = np.array(state[:]).reshape((1, 20))
    print(state)
    if np.random.rand() <= model.epsilon:
        return random.choice(actions)
    q_values = model.q_network.predict(state)
    action = np.argmax(q_values[0])
    print(f'Color: {game_color[i]}, Predict: {actions[action]}')
    state = []
    game_color.clear()
    game_num.clear()
    return action

def send_message_to_telegram_channel(text):
    print(text)
    message = ""
    if text == 2:
        message = "A próxima jogada é ⚫"
    elif text == 1:
        message = "A próxima jogada é 🔴"
    elif text == 0:
        message = "A próxima jogada é ⚪"
    elif text == 3:
        message = "Não sou capaz de prever a próxima jogada"

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
    return send_message_to_telegram_channel(predict())

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
        # Se inscreve no canal
        await client(JoinChannelRequest(group.id))
        # Inicia a escuta das mensagens
        print('Escutando mensagens do canal...')
        while True:
            messages = await client.get_messages(group.id, limit=1)
            message = messages[0]
            if message.message.strip().lower() == 'roll':
                getMachineGuess()
            await asyncio.sleep(2)
    else:
        print(f'Canal "{CHANNEL_LINK}" não encontrado')
        # Encerra a conexão
        await client.disconnect()

    
async def main():
    await listenMessages()

# Iniciar a execução da função main
asyncio.run(main())
