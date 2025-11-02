#!/bin/sh

# takes care of all the python venv stuff and lets you add this
# to a MCP server config using just one command without arguments

cd "$(dirname "$0")"
source venv/bin/activate
./main.py
