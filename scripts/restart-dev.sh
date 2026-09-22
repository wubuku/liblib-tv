#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_PORT="${DEV_PORT:-4317}"
PORT="$DEFAULT_PORT"

usage() {
  cat <<'EOF'
Usage:
  npm run dev:restart -- [PORT]
  npm run dev:restart -- --port PORT
  DEV_PORT=PORT npm run dev:restart

The command stops an existing Next.js dev server owned by this project on the
requested port, waits for the port to be released, and starts a fresh server.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

if [[ $# -eq 1 ]]; then
  if [[ "$1" == "--port" ]]; then
    usage >&2
    exit 2
  fi
  PORT="$1"
elif [[ $# -eq 2 ]]; then
  if [[ "$1" != "--port" ]]; then
    usage >&2
    exit 2
  fi
  PORT="$2"
fi

if [[ ! "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  printf 'Invalid port: %s\n' "$PORT" >&2
  exit 2
fi

if ! command -v lsof >/dev/null 2>&1; then
  printf 'Cannot inspect port %s: lsof is required on this macOS development setup.\n' "$PORT" >&2
  exit 1
fi

listener_pids() {
  lsof -nP -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | sort -u
}

process_snapshot() {
  ps -ww -o pid=,ppid=,command= -p "$1" 2>/dev/null | sed -E 's/^[[:space:]]+//'
}

parent_pid() {
  ps -o ppid= -p "$1" 2>/dev/null | tr -d ' '
}

process_belongs_to_project() {
  local pid="$1"
  local current="$pid"
  local depth=0
  local line

  while [[ -n "$current" && "$current" != "0" && "$depth" -lt 12 ]]; do
    line="$(process_snapshot "$current" || true)"
    if [[ "$line" == *"$PROJECT_ROOT"* ]]; then
      return 0
    fi
    if [[ "$line" == *"next dev"* || "$line" == *"/next-server"* || "$line" == *"next-server ("* ]]; then
      # A Next child may omit its working directory; keep walking ancestors
      # until the owning project command is found.
      :
    fi
    current="$(parent_pid "$current")"
    depth=$((depth + 1))
  done

  return 1
}

kill_project_listeners() {
  local pids=("$@")
  local pid
  local rejected=()
  local accepted=()

  for pid in "${pids[@]}"; do
    if process_belongs_to_project "$pid"; then
      accepted+=("$pid")
    else
      rejected+=("$pid")
    fi
  done

  if ((${#rejected[@]} > 0)); then
    printf 'Port %s is occupied by an unknown process; refusing to kill it:\n' "$PORT" >&2
    for pid in "${rejected[@]}"; do
      process_snapshot "$pid" >&2 || true
    done
    printf 'Choose another port or stop that process explicitly.\n' >&2
    exit 1
  fi

  if ((${#accepted[@]} == 0)); then
    return
  fi

  printf 'Stopping stale project dev server on port %s (PIDs: %s)\n' "$PORT" "${accepted[*]}"
  for pid in "${accepted[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done

  for _ in {1..50}; do
    if [[ -z "$(listener_pids)" ]]; then
      return
    fi
    sleep 0.1
  done

  local remaining
  remaining="$(listener_pids)"
  if [[ -n "$remaining" ]]; then
    printf 'Project dev server did not stop after SIGTERM; forcing stale listeners: %s\n' "$remaining"
    while read -r pid; do
      [[ -n "$pid" ]] && kill -KILL "$pid" 2>/dev/null || true
    done <<< "$remaining"
  fi
}

existing_pids="$(listener_pids || true)"
if [[ -n "$existing_pids" ]]; then
  existing_pid_array=()
  while read -r pid; do
    [[ -n "$pid" ]] && existing_pid_array+=("$pid")
  done <<< "$existing_pids"
  kill_project_listeners "${existing_pid_array[@]}"
fi

if [[ -n "$(listener_pids)" ]]; then
  printf 'Port %s is still occupied; refusing to start another server.\n' "$PORT" >&2
  exit 1
fi

cd "$PROJECT_ROOT"
printf 'Starting Next.js dev server on http://localhost:%s\n' "$PORT"
exec "$PROJECT_ROOT/node_modules/.bin/next" dev --port "$PORT"
