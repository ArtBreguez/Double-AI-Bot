import datetime
import json
import matplotlib.pyplot as plt
import os
from fpdf import FPDF
import matplotlib.dates as mdates

# Criar listas vazias para armazenar as informações relevantes
dates = []
colors_predicted = []
colors_real = []
results = []

with open('logs/requests.log', 'r') as f:
    data = f.read()

data = data.replace("'", '"')

with open('logs/requests_fixed.log', 'w') as f:
    f.write(data)

# Abrir o arquivo de texto
with open('logs/requests_fixed.log', 'r') as f:
    # Ler cada linha do arquivo
    for line in f:
        # Extrair as informações relevantes de cada linha
        line = line.strip()
        if line.startswith('INFO:root:'):
            line = line.replace('INFO:root:', '').strip()
            date_str, data_str = line.split('] ')
            date = datetime.datetime.strptime(date_str[1:], '%Y-%m-%d %H:%M:%S')
            data_dict = json.loads(data_str)
            colors_predicted.append(data_dict['predicted'])
            colors_real.append(data_dict['result'])
            results.append(data_dict['status'])
            dates.append(date)

# Criar gráfico de cores preditas X cores reais em forma de gráfico de barras empilhadas
colors = ['red', 'black', 'white']
victory_counts = {color: 0 for color in colors}
defeat_counts = {color: 0 for color in colors}

for i in range(len(colors_predicted)):
    color = colors_predicted[i]
    if results[i] == 'win':
        victory_counts[color] += 1
    elif results[i] == 'loss':
        defeat_counts[color] += 1

# Criar gráfico de barras empilhadas para vitória e derrota
fig, ax = plt.subplots()

bar_width = 0.5
opacity = 0.8

victory_bars = plt.bar(colors, [victory_counts[color] for color in colors],
                       bar_width, alpha=opacity, color='g', label='Vitória')

defeat_bars = plt.bar(colors, [defeat_counts[color] for color in colors],
                      bar_width, bottom=[victory_counts[color] for color in colors],
                      alpha=opacity, color='r', label='Derrota')

plt.xlabel('Cores')
plt.ylabel('Quantidade')
plt.title('Cores Previstas')
plt.xticks(colors)
plt.legend()
plt.tight_layout()
plt.savefig('logs/cores_previstas.png')
plt.clf()

# Criar gráfico de resultados
results_count = {'win': 0, 'loss': 0}
for result in results:
    results_count[result] += 1

colors = ['green', 'red']
labels = ['Vitórias', 'Derrotas']

plt.pie([results_count['win'], results_count['loss']], labels=labels, colors=colors, autopct='%1.1f%%')
plt.savefig('logs/win_loss_pie.png')
plt.clf()

# Inicializar as variáveis para contar o número de vitórias e derrotas
num_vitorias = 0
num_derrotas = 0

# Inicializar as listas para armazenar os dados para o gráfico
pontuacao = []
datas = []

# Percorrer as datas e os resultados para calcular a pontuação em cada ponto do tempo
for i, resultado in enumerate(results):
    if resultado == 'win':
        num_vitorias += 1
    else:
        num_derrotas += 1
    pontuacao.append(num_vitorias - num_derrotas)
    datas.append(dates[i])

# Plotar o gráfico de linha
fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.plot(datas, pontuacao)
ax.set_ylabel('Acertos')
ax.set_xlabel('Horário')
ax.set_title('Acertos ao longo do tempo')

# Adicionar linhas horizontais verdes e vermelhas para indicar a mudança de pontuação
for i in range(1, len(pontuacao)):
    if pontuacao[i] > pontuacao[i-1]:
        ax.axhline(y=pontuacao[i], color='green', alpha=0.5)
        ax.scatter(datas[i], pontuacao[i], color='green', s=100)
    else:
        ax.axhline(y=pontuacao[i], color='red', alpha=0.5)
        ax.scatter(datas[i], pontuacao[i], color='red', s=100)

plt.savefig('logs/timeline.png')
plt.clf()


# Obter a data atual
data_atual = datetime.date.today()

# Adicionar a data ao título
titulo = 'Relatório de performance ({})'.format(data_atual.strftime('%d/%m/%Y'))

# Adicionar o título ao PDF
class PDF(FPDF):
    def header(self):
        # Define a fonte para o cabeçalho
        self.set_font('Arial', 'B', 15)
        
        # Move para a direita
        self.cell(80)
        
        # Imprime o título do cabeçalho
        self.cell(30, 10, titulo, 0, 0, 'C')
        
        # Move para a próxima linha
        self.ln(20)

# Cria o objeto PDF e define o tamanho da página
pdf = PDF()
pdf.add_page()
pdf.set_font('Arial', '', 12)
pdf.set_margins(20, 20, 20)

# Percorre os arquivos da pasta "logs"
for filename in os.listdir("logs"):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        # Adiciona a imagem ao PDF
        pdf.image(os.path.join("logs", filename), w=180)
        
        # Move para a próxima linha
        pdf.ln(30)

# Salva o PDF em disco
pdf.output('logs/output.pdf', 'F')
