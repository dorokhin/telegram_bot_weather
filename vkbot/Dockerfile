FROM python:3.6-alpine

RUN adduser -D vkbot

WORKDIR /home/vkbot

RUN apk update
RUN apk upgrade
RUN apk --no-cache add \
    gcc \
    libffi-dev \
    openssl-dev \
    python3 \
    python3-dev \
    postgresql-client \
    postgresql-dev \
    build-base \
    gettext

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY . /home/vkbot

ENV FLASK_APP app.py

RUN chown -R vkbot:vkbot ./
USER vkbot
