FROM python:3.13-slim-bookworm

ARG SERVER=http://host.docker.internal:4111
ARG SERVER_API_VERSION=/api/v1
ARG UI_BASE_URL=http://host.docker.internal:3000

ENV SERVER=${SERVER}
ENV SERVER_API_VERSION=${SERVER_API_VERSION}
ENV UI_BASE_URL=${UI_BASE_URL}
ENV PLAYWRIGHT_TEST_BASE_URL=${UI_BASE_URL}

ENV DB_HOST=host.docker.internal
ENV DB_PORT=5433
ENV DB_NAME=nbank
ENV DB_USERNAME=postgres
ENV DB_PASSWORD=postgres

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN set -eux; \
    apt-get update -o Acquire::Retries=3 || \
    apt-get update -o Acquire::Retries=3 -o Acquire::AllowInsecureRepositories=true -o Acquire::AllowDowngradeToInsecureRepositories=true; \
    playwright install-deps; \
    playwright install; \
    rm -rf /var/lib/apt/lists/*

COPY . .

USER root

CMD ["pytest"]