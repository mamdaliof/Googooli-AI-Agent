# 🤖 Googooli Assistant: Open-Source Distribution Hub

Welcome to the **Googooli Assistant** open-source code package. Googooli is a personalized AI developer assistant, research proctor, and learning tutor designed to help index, tutor, and search notes, software projects, and papers. 

This hub consolidates the three implementation variants of the Googooli Assistant, providing a streamlined structure for configuration, diagnostics, and deployment across different target environments.

---

## 📂 Project Directory Structure

* **`config/`**: Contains global templates, including [`.env.example`](file:///home/farhad/googooli-assistant/config/.env.example) with all configuration variables.
* **`implementations/`**: Contains the source codes for the three variants:
  * [`obsidian-agy/`](file:///home/farhad/googooli-assistant/implementations/obsidian-agy/): The core Obsidian Vault gateway. Uses the Google Antigravity (`agy`) tool to interact directly with the vault.
  * [`openclaw/`](file:///home/farhad/googooli-assistant/implementations/openclaw/): A pure Python agent using Nvidia NIM for chat and system shell tools.
  * [`free-claude/`](file:///home/farhad/googooli-assistant/implementations/free-claude/): A FastAPI proxy that runs the Anthropic `claude` CLI (Claude Code) on top of Nvidia NIM, Google Gemini, or DeepSeek for free.

---

## ⚙️ Prerequisites & Required API Keys

Depending on the variant you choose, you will need to register and supply some of the following credentials in your `.env` file:

1. **Telegram Bot Token & Chat ID**
   * Create a bot using [@BotFather](https://t.me/BotFather) on Telegram and copy the token.
   * Send a message to [@userinfobot](https://t.me/userinfobot) to find your numeric **Telegram Chat ID** (this restricts bot access to just you).
2. **Nvidia NIM API Key**
   * Required for OpenClaw and Free Claude proxy. Register at [Nvidia Build](https://build.nvidia.com/) to get free inference credits.
3. **Tavily Search API Key**
   * Optional. Provides high-quality web-search API access for literature search and paper discovery.
4. **Google AI Studio Key**
   * Optional. Backs the Free Claude proxy with Gemini models.

---

## 🚀 Quick-Start Setup

To make setup as easy as possible, use our interactive launcher wizard:

1. **Navigate to the directory**:
   ```bash
   cd /home/farhad/googooli-assistant
   ```
2. **Run the Setup & Launcher wizard**:
   ```bash
   ./setup_googooli.sh
   ```
3. Follow the menu options (1, 2, or 3) to configure your chosen variant. The script will guide you through entering your API tokens, creating Python virtual environments, installing pip packages, and installing browser runtimes (like Playwright).
4. Run Option `4) Run Diagnostics Audit` to verify your python packages, environment variables, and system tools are functional.

---

## 🔬 Deployment Guide per Variant

### 1. Obsidian-Agy Gateway (Core Vault Variant)
This variant runs a Telegram bot connected directly to an Obsidian vault. It delegates user prompts to Google Antigravity (`agy`), allowing the bot to interact with daily notes, projects, and paper references.

* **Launch command**:
  ```bash
  cd implementations/obsidian-agy
  source .googooli/venv/bin/activate
  bash .googooli/scripts/run_gateway.sh
  ```
* **Interactive commands**:
  * `/start` - Start and show persistent bottom menu keyboard buttons.
  * `/clear` or `/reset` - Clear the active conversation history.
  * `/model` - Switch Gemini model dynamically.
  * `/diagnose_research` - Run dependency checks.
  * `/research <project>` - Spawn literature research background daemon.
  * `/get_report_summary <project>` - Fetch key summaries of compiled research notes.
  * `/get_report_full <project>` - Return the full research paper review.
  * *File Uploads* - Upload documents/photos/videos. The bot caches them and asks whether you want to save them to the Obsidian Inbox (`00-Inbox/temp/`).

### 2. OpenClaw Agent (Pure Python Variant)
A lightweight chatbot agent that uses Nvidia NIM for processing. It has access to shell tool executing capabilities, downloading files, using local search, and syncing notebook context.

* **Launch command**:
  ```bash
  cd implementations/openclaw
  source venv/bin/activate
  PYTHONPATH=. python3 src/run_telegram.py
  ```
* **Bot keyboard buttons**:
  * `📊 Project Status` - Scans local directories for active projects.
  * `🧹 Reset Session` - Clears chat history.

### 3. Free Claude Proxy (Claude Code Variant)
Acts as a local proxy. When you run `claude` (Claude Code CLI) or connect VS Code, the proxy intercepts Anthropic API calls and translates them to Nvidia NIM, Google Gemini, or DeepSeek API calls, bypassing paid billing restrictions.

* **Launch command**:
  ```bash
  cd implementations/free-claude
  source venv/bin/activate
  uvicorn server:app --host 0.0.0.0 --port 8082
  ```
* **Connect Client (Claude Code CLI)**:
  Configure Claude Code to point to the local proxy:
  ```bash
  export ANTHROPIC_API_KEY="dummy"
  export ANTHROPIC_BASE_URL="http://localhost:8082/api"
  claude
  ```
* **Connect Client (VS Code)**:
  Update your extension configuration to redirect the endpoint URL to `http://localhost:8082/api`.

---

## 🛠️ Modifications & Customizations
Before publishing this repository to open source, you can customize the code directly:
- To modify the **Obsidian bot behaviors**, edit: [`implementations/obsidian-agy/.googooli/scripts/telegram_gateway.py`](file:///home/farhad/googooli-assistant/implementations/obsidian-agy/.googooli/scripts/telegram_gateway.py).
- To add or modify **OpenClaw tools**, edit: [`implementations/openclaw/src/tools.py`](file:///home/farhad/googooli-assistant/implementations/openclaw/src/tools.py).
- To adjust the **Free Claude proxy mapping**, edit: [`implementations/free-claude/api/app.py`](file:///home/farhad/googooli-assistant/implementations/free-claude/api/app.py).

---

## 🤖 Working with AI Coding Agents (Claude Code, Cursor, Windsurf, Codex)

If developers prefer to customize or extend the Googooli Assistant using AI coding agents:
1. **Workspace Instruction file**: The workspace contains a root [AGENTS.md](file:///home/farhad/googooli-assistant/AGENTS.md) file.
2. **Automatic Bootstrap**: Modern coding assistants (like Claude Code, Cursor, Windsurf, and Codex) are configured to read [AGENTS.md](file:///home/farhad/googooli-assistant/AGENTS.md) automatically upon opening the workspace directory. The file instructs them on how to initialize the environments, run diagnostics, and implement new custom tools.
3. **Running the Agent**:
   * **Cursor/Windsurf**: Open this folder in the editor. You can use the composer or chat and reference `@AGENTS.md` for context.
   * **Claude Code**: Simply run `claude` inside the folder. It will read `AGENTS.md` (or `CLAUDE.md` which symlinks to it) and follow the conventions.

