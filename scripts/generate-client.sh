#! /usr/bin/env bash

set -e
set -x

cd backend
uv run python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > ../openapi.json
cd ..
mv openapi.json frontend/
cd frontend
bun run generate-client

# The SDK generator currently leaves spaces on otherwise blank lines. Normalize its output so
# generated changes pass the repository's whitespace checks and pre-commit hooks.
sed -i -E 's/[[:blank:]]+$//' src/lib/client/*.ts
