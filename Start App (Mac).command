#!/bin/bash
# ============================================================
#   AI Dashboard - Startup Script (macOS)
#   Double-click this file in Finder to run it.
# ============================================================

# Move into the folder this script lives in, regardless of
# where it was double-clicked from.
cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  AI Dashboard - Startup Script (macOS)"
echo "============================================================"
echo ""

# ------------------------------------------------------------
# 1. Verify Python is installed
# ------------------------------------------------------------
echo "[1/6] Checking for Python..."
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "[ERROR] Python was not found on this computer."
    echo "Please install Python 3.12 or newer from:"
    echo "  https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to close this window..."
    exit 1
fi

echo "      Found Python: $PYTHON_CMD"
echo "      Version: $($PYTHON_CMD --version)"
echo ""

# ------------------------------------------------------------
# 2. Create virtual environment if it doesn't exist
# ------------------------------------------------------------
echo "[2/6] Checking virtual environment..."
if [ ! -f "venv/bin/activate" ]; then
    echo "      No virtual environment found. Creating one now..."
    "$PYTHON_CMD" -m venv venv
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] Failed to create the virtual environment."
        echo "Try running this script again, or see INSTRUCTION.md."
        echo ""
        read -p "Press Enter to close this window..."
        exit 1
    fi
    echo "      Virtual environment created successfully."
else
    echo "      Virtual environment already exists."
fi
echo ""

# ------------------------------------------------------------
# 3. Activate the virtual environment
# ------------------------------------------------------------
echo "[3/6] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to activate the virtual environment."
    echo ""
    read -p "Press Enter to close this window..."
    exit 1
fi
echo "      Virtual environment activated."
echo ""

# ------------------------------------------------------------
# 4. Install missing dependencies
# ------------------------------------------------------------
echo "[4/6] Checking dependencies (this may take a minute the first time)..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to install dependencies from requirements.txt."
    echo "Check your internet connection and try again."
    echo ""
    read -p "Press Enter to close this window..."
    exit 1
fi
echo "      Dependencies are installed and up to date."
echo ""

# ------------------------------------------------------------
# 5. Verify the .env file exists
# ------------------------------------------------------------
echo "[5/6] Checking configuration file (.env)..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "      No .env file found. Creating one from .env.example..."
        cp ".env.example" ".env"
        echo ""
        echo "      A new .env file was created for you."
        echo "      IMPORTANT: Open .env in a text editor and add your"
        echo "      OPENAI_API_KEY to enable the AI Chat and Playground"
        echo "      features. See INSTRUCTION.md for step-by-step help."
        echo ""
    else
        echo "      [WARNING] No .env or .env.example file found."
        echo "      The app may not start correctly without one."
    fi
else
    echo "      .env file found."
    if grep -q "OPENAI_API_KEY=sk-your" ".env" 2>/dev/null; then
        echo "      [NOTICE] OPENAI_API_KEY still looks like the placeholder value."
        echo "      AI features will be disabled until you add a real key."
        echo "      See INSTRUCTION.md, section 12, for help."
    fi
fi
echo ""

# ------------------------------------------------------------
# 6. Launch the application
# ------------------------------------------------------------
echo "[6/6] Starting AI Dashboard..."
echo ""
echo "============================================================"
echo "  The app will open at:  http://127.0.0.1:5000"
echo "  Keep this window open while using the app."
echo "  Press CTRL+C in this window to stop the server."
echo "============================================================"
echo ""

# Give the server a moment to start, then open the browser.
( sleep 2 && open "http://127.0.0.1:5000" ) &

python app.py
APP_EXIT_CODE=$?

# ------------------------------------------------------------
# If the app exits or crashes, keep the window open so the
# user can read any error messages instead of it vanishing.
# ------------------------------------------------------------
echo ""
echo "============================================================"
if [ $APP_EXIT_CODE -ne 0 ]; then
    echo "  The application stopped with an error (exit code $APP_EXIT_CODE)."
    echo "  Scroll up to read any error messages above, or check the"
    echo "  Troubleshooting section of INSTRUCTION.md."
else
    echo "  The application has stopped."
fi
echo "============================================================"
read -p "Press Enter to close this window..."
