FROM python:3.12.6-slim

ENV SHELL="/bin/bash"

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends gcc \
  && apt-get install -y build-essential \
  && apt-get install -y pkg-config \
  && apt-get install -y libhdf5-dev \
  && apt-get install -y python3-tk \
  && apt-get install -y python3-pip \
  && apt-get install -y python3

RUN pip install --upgrade pip

# Set the working directory to /app
WORKDIR /app

COPY requirements.txt requirements.txt

## ----------------------------------------------------------------
## Install python packages
## ----------------------------------------------------------------
RUN pip install --no-cache-dir -r requirements.txt


COPY . .





