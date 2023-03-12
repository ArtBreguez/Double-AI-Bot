import json
import requests
import logging
import urllib
import yaml
import telethon
from telethon import TelegramClient
import asyncio
from telethon.tl.functions.channels import JoinChannelRequest
import numpy as np
import time
import threading
import pickle
from sklearn.preprocessing import LabelEncoder
import json
import re
from datetime import datetime
import pytz

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

game_color = []	
previous_payload = None
stream = 0
last_prediction = ''

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
model.epsilon = 0.03
def getBlazeData():
    global previous_payload, game_color
    try:
        response = requests.get(BLAZE)
        response.raise_for_status()
        data = response.json()
        payload = json.dumps(data["records"][:20])
        if payload == previous_payload:
            return None
        previous_payload = payload
        colors = ["red", "black", "white"]
        encoder = LabelEncoder().fit(colors)
        game_color = [encoder.transform([record["color"]])[0] for record in reversed(data["records"][:9])]
        return game_color
    except requests.exceptions.RequestException as e:
        print(f"Error getting data from blaze.com: {e}")


def predict(game_color):
    if np.random.rand() <= model.epsilon:
        return 'white'
    action = model.predict([game_color])
    global last_prediction
    last_prediction = action[0]
    return action[0]

def checkWin(game_color):
    global last_prediction
    if not last_prediction or not game_color:
        return

    color_dict = {1: 'red', 0: 'black', 2: 'white'}
    game_color_num = color_dict.get(game_color[-1])

    if game_color_num == last_prediction:
        log({"predicted": last_prediction, "result": game_color_num, "status": "win"})
    else:
        log({"predicted": last_prediction, "result": game_color_num, "status": "loss"})


def calculate_win_loss_percentage():
    win_count = loss_count = total_count = 0
    today = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d")
    with open('logs/requests.log', 'r') as f:
        for line in f:
            match = re.search(r"^INFO:root:\[([\d-]+ [\d:]+)\] {'predicted': '(\w+)', 'result': '(\w+)', 'status': '(\w+)'}", line)
            if match:
                log_date, predicted, result, status = match.groups()
                log_date = datetime.fromisoformat(log_date).astimezone(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d")
                if log_date == today:
                    if predicted == result and status == 'win':
                        win_count += 1
                    elif predicted != result and status == 'loss':
                        loss_count += 1
                    total_count += 1

    win_percentage = round(win_count / total_count * 100, 2) if total_count > 0 else 0.0
    loss_percentage = round(loss_count / total_count * 100, 2) if total_count > 0 else 0.0
    return win_percentage, loss_percentage, total_count


def send_message_to_telegram_channel(text):
    messages = {
        'black': "A próxima jogada é ⚫",
        'red': "A próxima jogada é 🔴",
        'white': "A próxima jogada é ⚪",
        'help': "👨🏼‍💻 Comandos disponíveis 🤖\n\n/start_stream - Inicia o stream de jogadas 🎰\n/stop_stream - Para o stream de jogadas 🛑\n/roll - Prediz a próxima jogada 🎲\n/statistics - Exibe as estatísticas de vitória/derrota 📈\n/last_plays - Exibe as últimas jogadas 🕹️",
        None: "👨🏼‍💻 Não há novas jogadas 🤖",
    }

    if text == "last_plays":
        getBlazeData()
        colors = game_color
        message = "👨🏼‍💻 Últimas jogadas 🤖\n\n" + convert_to_emoji(colors)
    elif "Estatísticas" in text:
        message = text 
    else:
        message = messages.get(text, "")

    encoded_message = urllib.parse.quote(message)
    url = "https://api.telegram.org/bot" + CHANNEL + "/sendMessage?chat_id=" + CHAT_ID + "&text=" + encoded_message

    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as e:
        logging.error("Error sending message to telegram channel: " + str(e))
        return


def convert_to_emoji(game_color):
    emojis = ['⚫', '🔴', '⚪']
    return ''.join([emojis[color] for color in game_color])

def log(message):
    try:
        with open('logs/requests.log', 'a') as file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f'[{timestamp}] {message}'
            logging.basicConfig(filename='logs/requests.log', level=logging.INFO)
            logging.info(log_message)
    except Exception as e:
        logging.error('Error writing to log file:', e)


def getMachineGuess():
    data = getBlazeData()
    if data is None:
        return send_message_to_telegram_channel(None)
    return send_message_to_telegram_channel(predict(data))

def startStream():
    global stream
    while stream:
        data = getBlazeData()
        if data:
            checkWin(data)
            send_message_to_telegram_channel(predict(data))
        time.sleep(3)

def stopStream():
    global stream
    stream = False

def startStreamInThread():
    threading.Thread(target=startStream).start()

async def listenMessages():
    # Caminho para o arquivo com o número de telefone e o código de autenticação
    session_file = 'session_name.session'

    # Inicializa o cliente e conecta ao Telegram
    async with TelegramClient(session_file, API_ID, API_HASH) as client:
        # Encontra o ID do grupo
        try:
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
                    command = message.message.strip().lower()
                    if command == '/roll':
                        getMachineGuess()
                    elif command == '/start_stream' and not stream:
                        stream = True
                        startStreamInThread()
                    elif command == '/stop_stream' and stream:
                        stopStream()
                    elif command == '/help':
                        send_message_to_telegram_channel('help')
                    elif command == '/statistics':
                        statistics = calculate_win_loss_percentage()
                        if statistics is None:
                            send_message_to_telegram_channel("Não há estatísticas disponíveis")
                        else:
                            send_message_to_telegram_channel(f"📈 Estatísticas 📈\n\nVitórias: {statistics[0]}%\nDerrotas: {statistics[1]}%\nTotal de jogadas: {statistics[2]}")
                    elif command == '/last_plays':
                        send_message_to_telegram_channel('last_plays')        
                    await asyncio.sleep(2)
            else:
                print(f'Canal "{CHANNEL_LINK}" não encontrado')
        except Exception as e:
            print(f"Erro ao obter informações do canal: {e}")
            return
    
async def main():
    await listenMessages()

# Iniciar a execução da função main
asyncio.run(main())
