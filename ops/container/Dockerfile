# =============================================================================
# XORAS SYSTEMS - SOVEREIGN LINUX CONTAINER BUILD SPECIFICATION
# Multi-Stage Production Linux Venv Architecture for Xoras Systems
# =============================================================================

FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV XORAS_HOME=/opt/xoras/SSOT_Agentic_Brain

# Install Linux system dependencies, GCC/AVX2 compilers, and Python 3.11 venv
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    curl \
    git \
    ffmpeg \
    espeak-ng \
    libespeak-ng-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create isolated Linux virtual environment (linyx venv)
RUN python3 -m venv /opt/xoras/venv
ENV PATH="/opt/xoras/venv/bin:$PATH"

# Install high-throughput Python dependencies inside Linux venv
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    numpy \
    soundfile \
    requests \
    flask \
    urllib3

# Set workspace working directory
WORKDIR /opt/xoras/SSOT_Agentic_Brain

# Copy Xoras SSOT codebase into container workspace
COPY . /opt/xoras/SSOT_Agentic_Brain

# Expose Port 8080 (Sovereign Stage) and Port 11434 (Inference Daemon)
EXPOSE 8080 11434

# Set container entrypoint
CMD ["/opt/xoras/venv/bin/python3", "ops/scripts/stage_server.py"]
