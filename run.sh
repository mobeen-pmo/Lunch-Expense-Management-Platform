#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -q streamlit pandas plotly

# Run the app
streamlit run app.py --server.port 8080 --server.address 0.0.0.0
