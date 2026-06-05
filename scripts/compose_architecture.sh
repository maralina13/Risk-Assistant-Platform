#!/usr/bin/env bash
set -euo pipefail

if docker compose version >/dev/null 2>&1; then
  docker compose -f docker-compose.architecture.yml up
  exit 0
fi

if command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f docker-compose.architecture.yml up
  exit 0
fi

cat <<'EOF'
Docker is installed, but Docker Compose is not available.

Try:
  open -a Docker
  docker compose version

If it still fails, restart Terminal or reinstall Docker Desktop.
EOF

exit 1
