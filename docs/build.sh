#!/usr/bin/env bash
set -euo pipefail

DOCS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$DOCS_DIR/.." && pwd)"
BUILD_DIR="$DOCS_DIR/_build/html"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Generate API references from Python docstrings for both language trees.
for lang in en ja; do
    rm -rf "$DOCS_DIR/$lang/api"
    mkdir -p "$DOCS_DIR/$lang/api"
    sphinx-apidoc --force --module-first \
        -o "$DOCS_DIR/$lang/api" \
        "$PROJECT_DIR/src/cap_inspector"
done

# English is also served at the Pages root.
sphinx-build -b html -c "$DOCS_DIR" "$DOCS_DIR/en" "$BUILD_DIR"
sphinx-build -b html -c "$DOCS_DIR" "$DOCS_DIR/en" "$BUILD_DIR/en"
sphinx-build -b html -c "$DOCS_DIR" "$DOCS_DIR/ja" "$BUILD_DIR/ja"
touch "$BUILD_DIR/.nojekyll"
