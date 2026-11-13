#!/usr/bin/env bash
set -euo pipefail

DOCS_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$DOCS_DIR/_build/html"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ルートは英語版を公開し、/en/ と /ja/ も独立して生成する。
sphinx-build -b html -c "$DOCS_DIR" "$DOCS_DIR/en" "$BUILD_DIR"
sphinx-build -b html -c "$DOCS_DIR" "$DOCS_DIR/en" "$BUILD_DIR/en"
sphinx-build -b html -c "$DOCS_DIR" "$DOCS_DIR/ja" "$BUILD_DIR/ja"
