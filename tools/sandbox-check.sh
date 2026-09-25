#!/usr/bin/env bash
# Render template.jsx against Homarr's real Custom JSX interpreter.
#
#   bash tools/sandbox-check.sh [ref]
#
# ref is any branch, tag or commit of homarr-labs/homarr that carries
# packages/custom-widgets (release/v2 onwards). Default: release/v2.
#
# Why a ref: the sandbox is not one fixed set of rules. Older builds implement
# == and != as string comparison, so a guard that works on one Homarr raises
# RUNTIME_RENDER_ERROR on another. Checking two refs is how you find that.
#
# Needs node, npx and network. Everything lands in .sandbox-check/, gitignored.
set -euo pipefail

REF="${1:-release/v2}"
WIDGET="."
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIDGET="$(cd "$WIDGET" && pwd)"
WORK="$ROOT/.sandbox-check/$(echo "$REF" | tr '/' '_')"
SRC="$WORK/src"

mkdir -p "$SRC"
if [ ! -f "$SRC/jsx/interpreter.tsx" ]; then
  echo "fetching packages/custom-widgets/src at $REF"
  API="https://api.github.com/repos/homarr-labs/homarr/git/trees/$REF?recursive=1"
  RAW="https://raw.githubusercontent.com/homarr-labs/homarr/$REF"
  curl -sf "$API" -o "$WORK/tree.json"
  python3 - "$WORK/tree.json" > "$WORK/files.txt" <<'PY'
import json, sys
tree = json.load(open(sys.argv[1]))["tree"]
prefix = "packages/custom-widgets/src/"
for entry in tree:
    path = entry["path"]
    if path.startswith(prefix) and entry["type"] == "blob" and "/test/" not in path:
        print(path)
PY
  count=0
  while read -r file; do
    rel="${file#packages/custom-widgets/src/}"
    mkdir -p "$SRC/$(dirname "$rel")"
    curl -sf "$RAW/$file" -o "$SRC/$rel" && count=$((count + 1))
  done < "$WORK/files.txt"
  echo "  $count files"
fi

cd "$WORK"
if [ ! -d node_modules/acorn ]; then
  echo "installing bundler dependencies"
  cat > package.json <<'JSON'
{ "name": "sandbox-check", "private": true, "version": "0.0.0" }
JSON
  npm install --silent --no-audit --no-fund acorn acorn-jsx react zod jsonpath-plus esbuild
fi

# The interpreter pulls component metadata that imports Mantine purely for
# types at runtime. Stub them so the bundle stays small and offline.
for pkg in @mantine/core @mantine/charts @mantine/dates @tabler/icons-react; do
  mkdir -p "node_modules/$pkg"
  echo '{"name":"stub","version":"0.0.0","main":"index.js"}' > "node_modules/$pkg/package.json"
  echo 'module.exports = new Proxy({}, { get: () => () => null });' > "node_modules/$pkg/index.js"
done

cat > entry.ts <<'TS'
export { renderSafeJsx } from "./src/jsx/interpreter";
export { createCustomJsxBindings } from "./src/jsx/bindings";
TS

npx --yes esbuild entry.ts --bundle --format=cjs --platform=node \
  --external:react --external:acorn --external:acorn-jsx \
  '--external:@mantine/*' '--external:@tabler/*' --external:jsonpath-plus \
  --alias:zod/v4=zod --outfile=bundle.cjs --log-level=error

echo "$(basename "$WIDGET") at $REF"
NODE_PATH="$WORK/node_modules" node "$ROOT/tools/sandbox-check.cjs" "$WORK/bundle.cjs" "$WIDGET/template.jsx" "$WIDGET/options.json" "$WIDGET/sandbox-cases.json"
