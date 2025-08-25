FROM python:3.12-alpine3.21

LABEL maintainer="sanyo.com"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt

COPY . /app

WORKDIR /app

EXPOSE 8000

ARG DEV=false

# pillow 충돌 방지.
RUN apk add -u zlib-dev jpeg-dev gcc musl-dev
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

ENV PATH="/py/bin:$PATH"

USER django-user
