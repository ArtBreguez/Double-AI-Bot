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
# import datetime
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
model.epsilon = 0.05
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
    # if np.random.rand() <= model.epsilon:
    #     return 'white'
    action = model.predict([game_color])
    global last_prediction
    last_prediction = action[0]
    return action[0]

def checkWin(game_color):
    print(game_color)
    global last_prediction
    if last_prediction == '' or last_prediction is None or game_color is None:
        return
    color_dict = {1:'red', 0:'black', 2:'white'}
    game_color_num = color_dict.get(game_color[-1])
    if game_color_num == last_prediction:
        log({"predicted": last_prediction, "result": game_color_num, "status": "win"})
    else:
        log({"predicted": last_prediction, "result": game_color_num, "status": "loss"})

def calculate_win_loss_percentage():
    # define o fuso horário local
    local_tz = pytz.timezone('America/Sao_Paulo')
    win_count = 0
    loss_count = 0
    today = datetime.now(local_tz).strftime("%Y-%m-%d")
    with open('logs/requests.log', 'r') as f:
        for line in f:
            match = re.search(r"^INFO:root:\[([\d-]+ [\d:]+)\] {'predicted': '(\w+)', 'result': '(\w+)', 'status': '(\w+)'}", line)
            if match:
                log_date, predicted, result, status = match.groups()
                # converte a data para o fuso horário local
                log_date = pytz.timezone('America/New_York').localize(datetime.strptime(log_date, "%Y-%m-%d %H:%M:%S")).astimezone(local_tz).strftime("%Y-%m-%d")
                if log_date == today:
                    if predicted == result and status == 'win':
                        win_count += 1
                    elif predicted != result and status == 'loss':
                        loss_count += 1
    total_count = win_count + loss_count
    win_percentage = round(win_count / total_count * 100, 2) if total_count > 0 else 0.0
    loss_percentage = round(loss_count / total_count * 100, 2) if total_count > 0 else 0.0
    return win_percentage, loss_percentage

def send_message_to_telegram_channel(text):
    message = ""
    if text == 'black':
        message = "A próxima jogada é ⚫"
    elif text == 'red':
        message = "A próxima jogada é 🔴"
    elif text == 'white':
        message = "A próxima jogada é ⚪"
    elif text == 'cmd':
        message = "👨🏼‍💻 Comandos disponíveis 🤖\n\n/start_stream - Inicia o stream de jogadas 🎰\n/stop_stream - Para o stream de jogadas 🛑\n/roll - Prediz a próxima jogada 🎲\n/statistics - Exibe as estatísticas de vitória/derrota 📈"
    elif text is None:
        message = "👨🏼‍💻 Não há novas jogadas 🤖"
    elif "Estatísticas" in text:
        message = text     

    encoded_message = urllib.parse.quote(message)
    url = "https://api.telegram.org/bot" + CHANNEL + "/sendMessage?chat_id=" + CHAT_ID + "&text=" + encoded_message

    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as e:
        logging.error("Error sending message to telegram channel: " + str(e))
        return

def log(message):
    try:
        file = open("logs/requests.log", "a")
    except:
        logging.error("Failed to open file logs/requests.log")
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    logging.basicConfig(filename="logs/requests.log", level=logging.INFO)
    logging.info(log_message)
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
        checkWin(data)
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
            if message.message.strip().lower() == '/cmd':
                send_message_to_telegram_channel('cmd')
            if message.message.strip().lower() == '/statistics':
                statistics = calculate_win_loss_percentage()
                print(statistics)
                if statistics is None:
                    send_message_to_telegram_channel("Não há estatísticas disponíveis")
                else:
                    send_message_to_telegram_channel(f"📈 Estatísticas 📈\n\nVitórias: {statistics[0]}%\nDerrotas: {statistics[1]}%")        
            await asyncio.sleep(2)
    else:
        print(f'Canal "{CHANNEL_LINK}" não encontrado')
        # Encerra a conexão
        await client.disconnect()

    
async def main():
    await listenMessages()

# Iniciar a execução da função main
asyncio.run(main())
