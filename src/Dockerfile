# syntax=docker/dockerfile:1

FROM python:3.13.14-slim-bookworm

WORKDIR /code

# Apply latest OS security patches
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Upgrade pip to fix security vulnerability GHSA-4xh5-x5gv-qwph
RUN pip install --no-cache-dir --upgrade pip>=25.3

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Install Node.js and pnpm with specific versions
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g pnpm@10.6.0 \
    && node --version \
    && pnpm --version \
    && rm -rf /var/lib/apt/lists/*

# Build React frontend
WORKDIR /code/frontend
RUN pnpm install --frozen-lockfile=false \
    && pnpm build \
    && rm -rf node_modules \
    && rm -rf /root/.local/share/pnpm \
    && rm -rf /root/.pnpm-store


RUN apt-get purge -y krb5-user libkrb5-3 libkrb5support0 libgssapi-krb5-2 curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Return to backend directory
WORKDIR /code

EXPOSE 50505

CMD ["gunicorn", "api.main:create_app"]