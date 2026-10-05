FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget curl git ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/SSOT_Agentic_Brain

# Copy core infrastructure
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire SSOT brain
COPY . .

# Run the 24/7 autonomous supervisor daemon
CMD ["python3", ".agents/skills/xmars-continuous-forge/scripts/xmars_forge.py", "supervisor"]
