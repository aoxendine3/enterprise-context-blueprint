#!/usr/bin/env bash
# Placeholder environment configuration for local DB access.
# -----------------------------------------------------------------
# This script is generated automatically because the original
# `zenith_env.sh` was missing from the backup. It provides safe defaults
# that allow the workspace to start without raising missing‑variable
# errors. Replace the placeholder values with the real secrets when they
# become available from the Council.
# -----------------------------------------------------------------

export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="exascale_dev"
export DB_USER="exascale_user"
export DB_PASSWORD="change_me_securely"

# Log a warning so operators know this is a temporary stub.
if [ "$DB_PASSWORD" = "change_me_securely" ]; then
  echo "[WARN] zenith_env.sh: using placeholder DB credentials. Replace with real secrets ASAP." >&2
fi
