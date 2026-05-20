FROM node:24-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    ffmpeg \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN npm install

RUN python3 -m venv /app/.venv
RUN /app/.venv/bin/pip install --upgrade pip
RUN /app/.venv/bin/pip install vosk imageio-ffmpeg

# Download and install Persian Vosk model
RUN rm -rf /app/python/models && \
    mkdir -p /app/python/models && \
    wget -O /tmp/vosk-model-fa-0.42.zip https://alphacephei.com/vosk/models/vosk-model-fa-0.42.zip && \
    unzip /tmp/vosk-model-fa-0.42.zip -d /app/python/model && \
    rm /tmp/vosk-model-fa-0.42.zip

RUN npm run build

EXPOSE 5171

ENV PORT=5171
ENV BODY_SIZE_LIMIT=50M
ENV PYTHON_BIN=/app/.venv/bin/python

CMD ["sh", "-lc", "node build --host 0.0.0.0 --port ${PORT:-5171}"]