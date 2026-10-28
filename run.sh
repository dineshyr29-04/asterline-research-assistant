#!/bin/sh
# Run after activating the documented Python environment and installing dependencies.
set -eu
cd "$(dirname "$0")"
exec python launch.py "$@"
