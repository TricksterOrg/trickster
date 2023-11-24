FROM python:3.11-slim

LABEL maintainer="jakub@tesarek.me"

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends python3-pip curl build-essential && \
    pip install --upgrade pip && \
    pip install poetry && \
    mkdir -p /app

WORKDIR /app
RUN poetry config virtualenvs.create false
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-interaction --no-ansi

COPY . /app

EXPOSE 8080

HEALTHCHECK CMD curl --fail http://localhost:8080/internal/healthcheck || exit 1

CMD ["uvicorn", "--factory", "trickster.trickster_app:create_app", "--host", "0.0.0.0", "--port", "8080"]
