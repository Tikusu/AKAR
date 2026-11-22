#!/usr/bin/env sh
set -eu
AKAR_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
find_python() {
    for AKAR_CANDIDATE in python3 python; do
        if command -v "$AKAR_CANDIDATE" >/dev/null 2>&1 && "$AKAR_CANDIDATE" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
            AKAR_PYTHON=$AKAR_CANDIDATE
            return 0
        fi
    done
    return 1
}
if ! find_python; then
    printf 'Menyiapkan Python untuk server web statis AKAR...\n'
    if command -v pkg >/dev/null 2>&1; then
        pkg install -y python
    elif command -v apt-get >/dev/null 2>&1; then
        if [ "$(id -u)" = 0 ]; then
            apt-get update
            apt-get install -y python3
        elif command -v sudo >/dev/null 2>&1; then
            sudo apt-get update
            sudo apt-get install -y python3
        else
            printf 'Instal Python 3.8+ terlebih dahulu, lalu jalankan skrip ini kembali.\n' >&2
            exit 1
        fi
    elif command -v brew >/dev/null 2>&1; then
        brew install python
    else
        printf 'Instal Python 3.8+ dari python.org, lalu jalankan kembali.\n' >&2
        exit 1
    fi
    find_python || { printf 'Python belum siap.\n' >&2; exit 1; }
fi
exec "$AKAR_PYTHON" "$AKAR_DIR/tools/serve.py" "$@"
