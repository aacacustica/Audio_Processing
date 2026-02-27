#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

docker run --rm -it \
  -v "${PROJECT_DIR}:/io" \
  -w /io \
  quay.io/pypa/manylinux_2_31_armv7l \
  bash
