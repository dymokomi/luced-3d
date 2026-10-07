#!/bin/sh
# This package's own tests (luce-base docs/CI.md): the programs under tests/, built with
# the development toolchain on PATH (luce-base tools/toolchain.py).
set -eu
cd "$(dirname "$0")"
base=$(command -v luce-base)
luce=$(command -v luce)
LUCE=$luce exec python3 tests/run.py "$@"
