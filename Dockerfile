FROM python:3.10.6-alpine

ENV PYTHONBUFFER=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add --no-cache mariadb-dev && apk add gettext
RUN pip3 install -r requirements.txt

COPY . /app