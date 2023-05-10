import datetime
import json
import matplotlib.pyplot as plt

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
plt.show()

# Criar gráfico de resultados
results_count = {'win': 0, 'loss': 0}
for result in results:
    results_count[result] += 1

colors = ['green', 'red']
labels = ['Vitórias', 'Derrotas']

plt.pie([results_count['win'], results_count['loss']], labels=labels, colors=colors, autopct='%1.1f%%')
plt.show()
