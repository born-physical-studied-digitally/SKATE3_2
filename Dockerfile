# Multi-Stage build setup
# - faster downloads & setup
# - smaller final production image

# Stage 1: Build stage using uv
FROM python:3.9-slim AS builder

# Copy Astral's offical uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set container working directory
WORKDIR /app

# Install system dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglx-mesa0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy config & metadata
COPY pyproject.toml README.md config.yaml ./

# Dummy src folder to prevent setup tools from crashing
RUN mkdir -p src/seismogram_pipeline && touch src/seismogram_pipeline/__init__.py

# Install dependencies using uv
# Persistent cache mount allows for fast rebuilds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache .

# Copy source code
COPY src ./src/

# Install the package using cache
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -e .


# Stage 2: Production stage

# Define Python Parent Image
FROM python:3.9-slim AS runner

WORKDIR /app

# Copy runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglx-mesa0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy site packages and binaries from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy config and source code
COPY config.yaml ./
COPY src/ ./src/

# Create directories for for input & output data
RUN mkdir -p /app/data/inputs /app/data/outputs

# Define default command for showing the help menu or run the CLI
ENTRYPOINT [ "seismogram-get-all-metadata" ]
CMD [ "--help" ]