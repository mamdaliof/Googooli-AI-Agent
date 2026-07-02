#!/bin/bash
# check_dependencies.sh - Diagnostics script for Googooli Research Assistant.

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "============================================================"
echo "🕵️ Googooli Research Assistant: Running Dependency Check..."
echo "============================================================"

# 1. Check Python version
echo -n "🐍 Python 3.12+: "
if command -v python3.12 &> /dev/null; then
    echo "OK ($(python3.12 --version))"
else
    echo "FAILED (Python 3.12 is missing. Needed for last30days-skill)"
fi

# 2. Check notebooklm CLI
echo -n "🧠 NotebookLM CLI: "
if command -v notebooklm &> /dev/null || command -v ~/.local/bin/notebooklm &> /dev/null; then
    echo "OK"
else
    echo "FAILED (notebooklm CLI not found in PATH or ~/.local/bin/)"
fi

# 3. Check NotebookLM Authentication
echo -n "🔑 NotebookLM Auth: "
if [ -f ~/.notebooklm/profiles/default/storage_state.json ]; then
    echo "OK"
else
    echo "WARNING (Auth state not found. Run 'notebooklm login')"
fi

# 4. Check Cloned Tools
echo -n "🛠️ Cloned last30days-skill: "
if [ -d "$BASE_DIR/tools/last30days-skill" ]; then
    echo "OK"
else
    echo "FAILED (last30days-skill not found in .googooli/tools/)"
fi

echo -n "📄 Cloned PaperCash: "
if [ -d "$BASE_DIR/tools/PaperCash" ]; then
    echo "OK"
else
    echo "FAILED (PaperCash not found in .googooli/tools/)"
fi

# 5. Check Python Libraries
echo "📦 Checking Python libraries..."
LIBS=("jieba" "requests" "bs4" "docx" "sqlite3")
for lib in "${LIBS[@]}"; do
    echo -n "   - $lib: "
    if python3.12 -c "import $lib" &> /dev/null; then
        echo "OK"
    else
        echo "MISSING (Will need to be installed on server)"
    fi
done

echo "============================================================"
echo "Diagnostics complete."
