FROM python:3.9-slim

ENV PYTHONPATH="/app/src"

WORKDIR /app

COPY requirements.txt . 

RUN pip3 install -r requirements.txt

WORKDIR /app/src

COPY src .

# add signal to stop the container
STOPSIGNAL SIGINT

CMD "python3" "main.py"