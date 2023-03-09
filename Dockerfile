FROM python:3.9.16-buster

WORKDIR /telegram-api

COPY requirements.txt .

RUN pip install logrus

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt 

COPY . .

ENTRYPOINT [ "python", "/telegram-api/app.py" ]
