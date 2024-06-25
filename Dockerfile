FROM python:3.11-slim-buster

RUN pip install --upgrade pip

RUN adduser --disabled-password worker
USER worker
WORKDIR /home/worker

COPY --chown=worker:worker requirements.txt requirements.txt

## ----------------------------------------------------------------
## Install python packages
## ----------------------------------------------------------------
RUN pip install --user --no-cache-dir -r requirements.txt

ENV PATH="/home/worker/.local/bin:${PATH}"

COPY --chown=worker:worker . .





