FROM python:3.8-slim

LABEL maintainer="jakub@tesarek.me"

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends python-pip curl

WORKDIR /app
COPY . /app
RUN pip install .

EXPOSE 8080

HEALTHCHECK CMD curl --fail http://localhost:8080${TRICKSTER_INTERNAL_PREFIX:-/internal}/health || exit 1

CMD ["gunicorn", "--config=gunicorn.conf.py", "app:app"]
