FROM python:3.12.6-slim

# Set the working directory to /app
WORKDIR /app

ENV SHELL="/bin/bash"

ARG USERNAME=disconnectome
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends gcc \
  && apt-get install -y build-essential \
  && apt-get install -y pkg-config \
  && apt-get install -y libhdf5-dev \
  && apt-get install -y python3-tk

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && chown -R ${USER_UID}:${USER_GID} /app

USER $USERNAME


COPY --chown=${USER_UID}:${USER_GID} requirements.txt requirements.txt

## ----------------------------------------------------------------
## Install python packages
## ----------------------------------------------------------------
RUN pip install --no-cache-dir -r requirements.txt


COPY --chown=${USER_UID}:${USER_GID} . .






