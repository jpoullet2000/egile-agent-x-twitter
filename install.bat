@echo off
echo Installing egile-agent-x-twitter...

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.10+ is required. Install from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create venv
echo Creating virtual environment...
python -m venv .venv

REM Activate
call .venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
pip install -e .[all]

REM Create env file if missing
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo Edit .env with your API keys (X/Twitter + LLM).
)

echo.
echo Installation complete.
echo To run: python -m egile_agent_x_twitter.run_server
pause
