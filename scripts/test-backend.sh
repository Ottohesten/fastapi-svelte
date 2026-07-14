#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project_name="fastapi-svelte-tests-$(id -u)-$$"
compose=(
    docker compose
    --project-name "$project_name"
    --file "$repo_root/compose.test.yaml"
)

cleanup() {
    "${compose[@]}" down --rmi local --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

"${compose[@]}" up --detach --wait test-db
"${compose[@]}" run --build --rm --no-deps backend-tests "$@"
