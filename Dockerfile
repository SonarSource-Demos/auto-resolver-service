FROM python:3.11-slim

EXPOSE 8080

RUN apt-get --assume-yes update && apt-get --assume-yes install bash

RUN mkdir /apps && \
    mkdir /apps/app && \
    mkdir /apps/conf && \
    mkdir /apps/files && \
    mkdir /apps/startup && \
    mkdir /apps/settings && \
    mkdir /apps/settings/env && \
    mkdir /apps/settings/secrets && \
    mkdir /apps/settings/test

COPY requirements.txt /apps/requirements.txt

RUN pip install -r /apps/requirements.txt
COPY /deployment/conf/ /apps/conf/
COPY /deployment/startup /apps/startup
COPY /app /apps/app/

RUN chmod +x /apps/startup/app.sh && \
    chmod +x /apps/startup/test.sh

WORKDIR /apps/app