# Download base image ubuntu 20.04
FROM ubuntu:20.04

LABEL maintainer="gennadiy.donchyts@gmail.com"
LABEL version="1.0"
LABEL description="This is custom Docker Image for the preparation of QGIS EE plugin dependencies for Ubuntu."

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN apt update

# Install Python 3.7
RUN apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
WORKDIR /tmp
RUN wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz
RUN tar -xf Python-3.7.0.tgz
WORKDIR /tmp/Python-3.7.0
RUN ./configure
RUN make
RUN make install

# RUN make install
RUN python3 --version

RUN apt install -y git

WORKDIR /tmp
RUN git clone https://github.com/gee-community/qgis-earthengine-plugin.git
WORKDIR /tmp/qgis-earthengine-plugin

RUN pip3 install paver

RUN paver setup
RUN paver package

