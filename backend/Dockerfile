FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    stockfish \
    && rm -rf /var/lib/apt/lists/* \
    && (ls -la /usr/games/stockfish || ls -la /usr/bin/stockfish || which stockfish || echo "STOCKFISH NOT FOUND IN BUILD")

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add /usr/games to PATH so shutil.which() can find stockfish installed by apt
ENV PATH="/usr/games:${PATH}"
ENV STOCKFISH_PATH=/usr/games/stockfish

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
