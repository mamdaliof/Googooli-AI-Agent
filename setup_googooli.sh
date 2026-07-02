#!/bin/bash
# =========================================================================
#             GOOGOOLI ASSISTANT - UNIFIED LAUNCHER & SETUP WIZARD
# =========================================================================

# Text styling
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$BASE_DIR/config"
IMPL_DIR="$BASE_DIR/implementations"

clear
echo -e "${CYAN}${BOLD}=========================================================================${NC}"
echo -e "${CYAN}${BOLD}           🤖 Welcome to Googooli Assistant Distribution Hub 🤖          ${NC}"
echo -e "${CYAN}${BOLD}=========================================================================${NC}"
echo -e "This wizard helps you configure, audit, and launch your preferred variant."
echo

show_menu() {
    echo -e "${BOLD}Please select an implementation variant to configure or run:${NC}"
    echo -e "1) ${BOLD}Obsidian-Agy Gateway${NC} (Core vault gateway, requires Antigravity agy/gemini CLI)"
    echo -e "2) ${BOLD}OpenClaw Agent${NC} (Self-contained Python agent, requires NVIDIA NIM API)"
    echo -e "3) ${BOLD}Free Claude Proxy & Agent${NC} (Runs Claude Code CLI proxy on alternative backends)"
    echo -e "4) ${BOLD}Run Diagnostics Audit${NC} (Check environment, libraries, and API keys)"
    echo -e "5) ${BOLD}Exit${NC}"
    echo
    echo -n "Select option [1-5]: "
}

setup_env_file() {
    local target_env="$1"
    local vars=("${@:2}")
    
    if [ -f "$target_env" ]; then
        echo -e "${GREEN}✅ Environment file already exists at: $(basename $(dirname "$target_env"))/.env${NC}"
        return 0
    fi

    echo -e "${YELLOW}📝 Setting up configuration variables...${NC}"
    mkdir -p "$(dirname "$target_env")"
    touch "$target_env"

    for var in "${vars[@]}"; do
        echo -n "Enter value for $var: "
        read -r val
        echo "$var=\"$val\"" >> "$target_env"
    done
    echo -e "${GREEN}✅ Created env config file!${NC}"
}

setup_obsidian_agy() {
    local variant_dir="$IMPL_DIR/obsidian-agy"
    echo -e "\n${BLUE}${BOLD}--- Configuring Obsidian-Agy Gateway ---${NC}"
    
    # 1. Check/create Env
    local env_path="$variant_dir/.googooli/config/.env"
    setup_env_file "$env_path" "GOOGOOLI_TELEGRAM_TOKEN" "GOOGOOLI_CHAT_ID" "TAVILY_API_KEY"

    # 2. Venv setup
    echo -e "\n${YELLOW}📦 Creating Python Virtual Environment...${NC}"
    python3 -m venv "$variant_dir/.googooli/venv"
    source "$variant_dir/.googooli/venv/bin/activate"
    
    # 3. Pip install
    echo -e "📥 Installing Python dependencies..."
    pip install --upgrade pip
    pip install pyTelegramBotAPI markdown2 requests beautifulsoup4 python-docx jieba tavily-python

    # 4. Init SQLite
    echo -e "🗄️ Initializing tracking database..."
    python3 "$variant_dir/.googooli/scripts/init_db.py"
    
    echo -e "${GREEN}${BOLD}✅ Setup completed!${NC}"
    echo -e "To start the gateway bot run:"
    echo -e "${CYAN}cd $variant_dir && source .googooli/venv/bin/activate && bash .googooli/scripts/run_gateway.sh${NC}\n"
    deactivate
}

setup_openclaw() {
    local variant_dir="$IMPL_DIR/openclaw"
    echo -e "\n${BLUE}${BOLD}--- Configuring OpenClaw Agent ---${NC}"
    
    # 1. Check/create Env
    local env_path="$variant_dir/.env"
    setup_env_file "$env_path" "TELEGRAM_BOT_TOKEN" "NVIDIA_API_KEY" "TAVILY_API_KEY"

    # 2. Venv setup
    echo -e "\n${YELLOW}📦 Creating Python Virtual Environment...${NC}"
    python3 -m venv "$variant_dir/venv"
    source "$variant_dir/venv/bin/activate"

    # 3. Pip install
    echo -e "📥 Installing Python dependencies..."
    pip install --upgrade pip
    pip install requests pyTelegramBotAPI python-dotenv notebooklm-py playwright

    # 4. Playwright browsers
    echo -e "🌐 Installing browser binaries (Playwright)...${NC}"
    python3 -m playwright install chromium

    echo -e "${GREEN}${BOLD}✅ Setup completed!${NC}"
    echo -e "To run the OpenClaw bot run:"
    echo -e "${CYAN}cd $variant_dir && source venv/bin/activate && PYTHONPATH=. python3 src/run_telegram.py${NC}\n"
    deactivate
}

setup_free_claude() {
    local variant_dir="$IMPL_DIR/free-claude"
    echo -e "\n${BLUE}${BOLD}--- Configuring Free Claude Proxy & Agent ---${NC}"
    
    # 1. Check/create Env
    local env_path="$variant_dir/.env"
    setup_env_file "$env_path" "NVIDIA_NIM_API_KEY" "GEMINI_API_KEY" "DEEPSEEK_API_KEY"

    # 2. Venv setup
    echo -e "\n${YELLOW}📦 Creating Python Virtual Environment...${NC}"
    python3 -m venv "$variant_dir/venv"
    source "$variant_dir/venv/bin/activate"

    # 3. Pip install
    echo -e "📥 Installing Python dependencies from setup schema..."
    pip install --upgrade pip
    pip install fastapi uvicorn httpx pydantic python-dotenv tiktoken python-telegram-bot discord.py pydantic-settings openai loguru aiohttp jsonschema markdown-it-py

    # 4. Optional Googooli agent under Free Claude setup
    echo -n "Do you also want to setup the nested Googooli Agent bot? [y/N]: "
    read -r ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        local agent_env="$variant_dir/googooli_agent/.env"
        setup_env_file "$agent_env" "TELEGRAM_BOT_TOKEN" "NVIDIA_API_KEY" "TAVILY_API_KEY"
        
        python3 -m venv "$variant_dir/googooli_agent/venv"
        source "$variant_dir/googooli_agent/venv/bin/activate"
        pip install requests pyTelegramBotAPI python-dotenv notebooklm-py playwright
        python3 -m playwright install chromium
        deactivate
    fi

    echo -e "${GREEN}${BOLD}✅ Setup completed!${NC}"
    echo -e "To run the Free Claude Proxy server run:"
    echo -e "${CYAN}cd $variant_dir && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8082${NC}"
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        echo -e "To run the nested Googooli bot run:"
        echo -e "${CYAN}cd $variant_dir/googooli_agent && source venv/bin/activate && PYTHONPATH=. python3 run_telegram.py${NC}"
    fi
    echo
}

run_diagnostics() {
    echo -e "\n${BLUE}${BOLD}--- Starting Diagnostics Audit ---${NC}"
    
    # Check Python version
    echo -n "🐍 Python 3.12+ status: "
    if command -v python3 &> /dev/null; then
        local version=$(python3 --version | awk '{print $2}')
        echo -e "${GREEN}OK (Detected Python $version)${NC}"
    else
        echo -e "${RED}FAILED (python3 command not found)${NC}"
    fi

    # Check Git
    echo -n "📂 Git installation status: "
    if command -v git &> /dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}WARNING (git is missing, sync features might be degraded)${NC}"
    fi

    # Check Node.js
    echo -n "🟢 Node.js installation status: "
    if command -v node &> /dev/null; then
        echo -e "${GREEN}OK (Detected Node $(node -v))${NC}"
    else
        echo -e "${YELLOW}WARNING (Node.js/npm is missing, context7 tools will be disabled)${NC}"
    fi

    # Check Antigravity CLI
    echo -n "🛡️ Antigravity CLI (agy) status: "
    if command -v agy &> /dev/null || command -v antigravity &> /dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}WARNING (agy command not found in PATH; Obsidian-Agy will fall back to legacy mode)${NC}"
    fi

    echo -e "${CYAN}Audit complete! Please make sure your .env configurations are set up correctly before launching bots.${NC}\n"
}

while true; do
    show_menu
    read -r choice
    case $choice in
        1) setup_obsidian_agy ;;
        2) setup_openclaw ;;
        3) setup_free_claude ;;
        4) run_diagnostics ;;
        5) echo -e "\n${GREEN}Goodbye! Enjoy your Googooli Assistant!${NC}"; exit 0 ;;
        *) echo -e "\n${RED}Invalid option, please choose between 1 and 5.${NC}\n" ;;
    esac
done
