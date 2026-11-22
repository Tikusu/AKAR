#!/usr/bin/env sh
set -eu
AKAR_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec sh "$AKAR_DIR/MULAI-AKAR.sh" --stop
