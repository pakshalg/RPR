#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
"$DIR/venv/Scripts/streamlit" run "$DIR/App/main.py"
