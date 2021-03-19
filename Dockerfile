FROM python:3.8-buster

LABEL maintainer="jakub@tesarek.me"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

WORKDIR /app
COPY . /app
RUN pip install .

EXPOSE 5000

HEALTHCHECK CMD curl --fail http://localhost:5000/internal/health || exit 1

CMD ["gunicorn", "--config=gunicorn.conf.py", "app:app"]
