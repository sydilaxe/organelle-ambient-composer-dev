#!/bin/bash
# Regenerate patches/Amble from the Python sources.
set -e
cd "$(dirname "$0")"
python3 gen.py
