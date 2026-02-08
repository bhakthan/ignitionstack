FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Copy source first (templates + ignition package needed for install)
COPY . .

# Install Python deps
RUN pip install --no-cache-dir .

ENTRYPOINT ["ignition"]
CMD ["--help"]
