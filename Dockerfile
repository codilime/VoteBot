FROM python:3.10.5-slim-bullseye AS build

ARG SECRET_KEY
ARG DATABASE_URL
ARG SIGNING_SECRET
ARG SLACK_BOT_TOKEN
ARG ENABLE_SCHEDULER

ENV SECRET_KEY=${SECRET_KEY}
ENV DATABASE_URL=${DATABASE_URL}
ENV SIGNING_SECRET=${SIGNING_SECRET}
ENV SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
ENV ENABLE_SCHEDULER=${ENABLE_SCHEDULER}

WORKDIR /votebot

COPY requirements/prod.txt ./requirements.txt
RUN pip install -r requirements.txt --no-cache-dir && \
    adduser lime && \
    chown -R lime /votebot

COPY bot_app ./bot_app
COPY bot_project ./bot_project
COPY manage.py ./


FROM build AS production

USER lime
ENTRYPOINT gunicorn bot_project.wsgi:application -b 0.0.0.0:8000 --timeout 5


FROM build AS tests

COPY requirements/dev.txt ./requirements.txt
COPY tests ./tests

RUN pip install -r requirements.txt --no-cache-dir

USER lime
ENTRYPOINT coverage run --source='./bot_app' manage.py test --verbosity=3 && coverage report -m
