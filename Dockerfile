FROM python:3.9.15-buster

RUN apt-get update
RUN apt-get install git

RUN mkdir app
WORKDIR /app

RUN git clone https://github.com/modoboa/modoboa-installer.git
WORKDIR /app/modoboa-installer/
