FROM python:3.12-alpine

WORKDIR /app

COPY CustomModules ./CustomModules
COPY *.py .
COPY requirements.txt .

ENV TERM=xterm
ENV PYTHONUNBUFFERED=1

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT

RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libc-dev linux-headers rust cargo g++ && \
    apk add curl && \
    python -m pip install --root-user-action --upgrade pip && \
    pip install --root-user-action --upgrade setuptools wheel && \
    pip install --root-user-action -r requirements.txt && \
    apk del .build-deps && \
    find /usr/local \
    \( -type d -a -name test -o -name tests \) \
    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip

LABEL maintainer="Discord: piko.piko.no.mi (970119359840284743)" \
      commit=$COMMIT \
      description="Basic discord.py setup." \
      release=$BUILD_DATE \
      VERSION="1.0.0" \
      url="https://gitlab.bloodygang.com/Serpensin/Basis"

CMD ["python3", "main.py"]
