FROM node:24-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN npm install

RUN python3 -m venv /app/.venv
RUN /app/.venv/bin/pip install --upgrade pip
RUN /app/.venv/bin/pip install vosk imageio-ffmpeg

RUN npm run build

EXPOSE 5171

ENV PORT=5171
ENV BODY_SIZE_LIMIT=50M
ENV PYTHON_BIN=/app/.venv/bin/python

CMD ["sh", "-lc", "node build --host 0.0.0.0 --port ${PORT:-5171}"]