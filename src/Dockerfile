# syntax=docker/dockerfile:1

FROM python:3.13.8-slim-bookworm

WORKDIR /code

COPY . .


RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Install Node.js and pnpm with specific versions
RUN apt-get update \
    && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pnpm@10.4.1 \
    && node --version \
    && pnpm --version

# Build React frontend
WORKDIR /code/frontend
RUN pnpm install \
    && pnpm build


RUN apt-get purge -y krb5-user libkrb5-3 libkrb5support0 libgssapi-krb5-2

# Return to backend directory
WORKDIR /code

EXPOSE 50505

CMD ["gunicorn", "api.main:create_app"]