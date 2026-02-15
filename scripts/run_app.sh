#!/bin/bash
# Navigate to project root (parent of this script)
cd "$(dirname "$0")/.."

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment 'venv' not found! Please create it first in the project root."
    exit 1
fi

# Run App
shiny run --reload app.py
