FROM python:3.8-buster

MAINTAINER Jakub Tesárek "jakub@tesarek.me"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

WORKDIR /app
COPY . /app
RUN pip install .

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
