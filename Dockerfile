FROM python:3.9.16-buster
WORKDIR /telegram-api
COPY . .
RUN pip install --upgrade pip
RUN pip install tensorflow
RUN pip install ioutil
RUN pip install logrus
RUN pip install telethon
RUN pip install pyyaml
RUN pip install urllib3
RUN pip install asyncio
RUN pip install send2trash
EXPOSE 5000
ENTRYPOINT [ "python", "/telegram-api/use-model.py" ]