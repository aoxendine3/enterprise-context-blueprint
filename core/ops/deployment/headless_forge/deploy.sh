#!/bin/bash
echo "Deploying Sovereign 22-Agent Forge to off-grid headless server..."
docker-compose up -d --build
echo "Forge is now running autonomously in the background."
