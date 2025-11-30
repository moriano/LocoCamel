#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment and run Flask app
source .venv/bin/activate
python app.py
