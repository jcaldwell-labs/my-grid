#!/usr/bin/env bash
# Simple wrapper to run demo - easier for VHS to call
cd "$(dirname "$0")"
python3 -c "import sys; sys.path.insert(0, 'src'); from demo import run_demo; run_demo(60)"
