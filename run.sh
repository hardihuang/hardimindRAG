#!/bin/bash
# Knowledge Search — Quick Start Script

set -e

echo "=========================================="
echo "  Knowledge Search — RAG + Semantic Search"
echo "=========================================="
echo ""

# Install dependencies
echo "[1/2] Installing dependencies..."
pip3 install -r "$(dirname "$0")/requirements.txt" -q

echo ""
echo "[2/2] Starting Streamlit app..."
echo ""

# Start Streamlit
streamlit run "$(dirname "$0")/app.py"
