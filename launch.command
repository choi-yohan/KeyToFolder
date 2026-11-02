#!/bin/bash
# macOS: double-click. Linux: bash launch.command
cd -- "$(dirname -- "$0")" || exit 1

run_if_supported() {
    [ -x "$1" ] || return 1
    "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 || return 1
    exec "$1" app.py
}

# Prefer a project virtual environment, then the user's installed Python.
run_if_supported "$PWD/.venv/bin/python3"
python_on_path="$(command -v python3 2>/dev/null)"
if [ -n "$python_on_path" ]; then
    run_if_supported "$python_on_path"
fi
# Finder can launch with a shorter PATH than an interactive terminal.
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    run_if_supported "$candidate"
done
printf '%s\n' 'Python 3.10 or newer is required.' 'Install it from https://www.python.org/downloads/ and launch again.'
printf '%s' 'Press Enter to close this window... '
read -r _
exit 1
