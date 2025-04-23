FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

ENV SHELL="/bin/bash"

ARG USERNAME=disconnectome
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get autoclean && \
  apt-get install -y --no-install-recommends gcc \
  build-essential \
  pkg-config \
  libhdf5-dev \
  python3-tk \
  cmake \
  xvfb \
  libegl1-mesa \
  x11-xserver-utils \
  libxkbcommon-x11-0 \
  x11-utils && \
  apt-get clean && \
  rm -rf /var/cache/apk/*

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && chown -R ${USER_UID}:${USER_GID} /app

USER $USERNAME


COPY --chown=${USER_UID}:${USER_GID} requirements.txt requirements.txt

## ----------------------------------------------------------------
## Install python packages
## ----------------------------------------------------------------
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


COPY --chown=${USER_UID}:${USER_GID} . .






