FROM python:3.6

ENV PYTHONUNBUFFERED 1

# libmagic: file format detection
RUN apt-get update && apt-get install -y libmagic-dev

RUN adduser --gecos "User for running app as non-root" --shell /bin/bash --disabled-password lzupload

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /requirements/production.txt \
    && rm -rf /requirements

COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint
RUN chown lzupload /entrypoint

COPY ./compose/production/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start
RUN chown lzupload /start

COPY ./compose/production/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r//' /start-celeryworker
RUN chmod +x /start-celeryworker
RUN chown lzupload /start-celeryworker

COPY ./compose/production/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r//' /start-celerybeat
RUN chmod +x /start-celerybeat
RUN chown lzupload /start-celerybeat

COPY ./compose/production/django/celery/flower/start /start-flower
RUN sed -i 's/\r//' /start-flower
RUN chmod +x /start-flower

# TODO: Special deployment note: build JS assets before making container? (this could be done better)
#   Ask Jacob for best approach here: multistage builds etc
COPY . /app

RUN chown -R lzupload /app

USER lzupload
RUN mkdir /lz-uploads
RUN chown lzupload /lz-uploads

WORKDIR /app

# TODO: add a JS build step. Eg:
#    https://medium.com/@shakyShane/lets-talk-about-docker-artifacts-27454560384f

ENTRYPOINT ["/entrypoint"]
