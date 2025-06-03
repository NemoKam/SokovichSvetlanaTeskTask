FROM python:3.13.3-bookworm

WORKDIR /app

COPY requirements.txt /app/

RUN apt clean -y
RUN apt update -y
RUN apt install dos2unix -y

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

COPY . /app/

RUN chmod u+x /app/entrypoint.sh
# dos2unix для безопасности при переносе содержимого файла 
RUN dos2unix /app/entrypoint.sh

CMD ["./entrypoint.sh"]
