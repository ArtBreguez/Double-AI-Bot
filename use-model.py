import json
import requests
import os
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
from tensorflow import keras
import numpy as np

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


latestColor = ""

def read_config(file):
    with open(file, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            channel = config['Channel']
            chat_id = config['ChatID']
            blaze = config['Blaze']
            API_HASH = config['API_HASH']
            API_ID = config['API_ID']
            CHANNEL_LINK = config['CHANNEL_LINK']
            return channel, chat_id, blaze, API_HASH, API_ID, CHANNEL_LINK
        except yaml.YAMLError as e:
            print(e)

channel, chat_id, blaze, API_HASH, API_ID, CHANNEL_LINK = read_config('config.yml')
model = keras.models.load_model('model.h5')

def getBlazeData():
    colors = []
    data = requests.get(blaze)
    if data.status_code != 200:
        raise Exception("Error getting data from blaze.com")
    result = TotalPages(0, [])
    result = json.loads(data.text)
    for i, v in enumerate(result["records"]):
        if i == 14:
            break
        colors.append(v["color"])
    colors = list(reversed(colors))
    return colors

def convert_to_numbers(colors):
    color_map = {'white': 0, 'red': 1, 'black': 2}
    numbers = [color_map[color] for color in colors]
    input_data = ",".join(str(num) for num in numbers)
    return {"input": input_data}


def predict(input_data):
    # Transforma a entrada em um formato apropriado para ser utilizado como entrada do modelo
    input_data = np.array([[int(x) for x in input_data.split(',')]])

    # Utiliza o modelo para fazer uma previsão com base na entrada recebida
    prediction = model.predict(input_data)

    # Transforma a saída da previsão em uma resposta HTTP
    response = str(np.argmax(prediction[0]))
    print(response)
    return response


def send_message_to_telegram_channel(text):
    emoji = ""
    message = ""
    if text == "2":
        emoji = "⚫"
    elif text == "1":
        emoji = "🔴"
    elif text == "0":
        emoji = "⚪"
    elif text == "Win":
        emoji = "Win 🏆"
    elif text == "Loss":
        emoji = "Loss 👎"
    else:
        return

    if emoji == "🏆":
        message = "Win " + emoji
    elif emoji == "👎":
        message = "Loss " + emoji
    else:
        message = "A próxima jogada é " + emoji

    encoded_message = urllib.parse.quote(message)
    url = "https://api.telegram.org/bot" + channel + "/sendMessage?chat_id=" + chat_id + "&text=" + encoded_message

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
    input = convert_to_numbers(getBlazeData())
    print()
    return send_message_to_telegram_channel(predict(input['input']))

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
