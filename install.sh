#!/bin/bash
set -e

echo "Installing egile-agent-x-twitter..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10+ is required" >&2
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[all]

if [ ! -f .env ]; then
  echo "Creating .env from template..."
  cp .env.example .env
  echo "Edit .env with your API keys (X/Twitter + LLM)."
fi

echo "Installation complete."
echo "To run: python -m egile_agent_x_twitter.run_server"
