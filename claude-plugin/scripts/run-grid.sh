#!/bin/bash
# Wrapper script for running my-grid plugin CLI
# This script is invoked by the /grid command

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PLUGIN_DIR/src"

# Run the CLI with all arguments
exec python3 "$SRC_DIR/cli.py" "$@"
