# 🤖 AI Agent System Instructions (AGENTS.md)

Welcome, AI Agent! You are running inside the **Googooli Assistant Distribution Hub** workspace. This document outlines the project architecture, initialization procedures, tool integrations, and constraints to help you bootstrap this workspace and remain compatible with its codebase.

---

## 📂 Project Architecture Overview

This project consolidates three implementations of the Googooli Assistant:
1. **`implementations/obsidian-agy/`**: Integrates a Telegram bot gateway with an Obsidian vault using the Google Antigravity (`agy` or `gemini`) CLI.
2. **`implementations/openclaw/`**: Standalone Python agent utilizing Nvidia NIM for chat completion and tool calling.
3. **`implementations/free-claude/`**: FastAPI proxy translating Anthropic Claude Code CLI requests into Nvidia NIM/Gemini completions.

---

## 🚀 Setup & Initialization Commands

To initialize or audit the environment, you (the agent) can run the following commands:

### 1. Unified Environment Setup & Wizard
Execute the main launcher script to create python virtual environments, download packages, and configure variables:
* **Interactive mode (via user input)**:
  ```bash
  ./setup_googooli.sh
  ```
* **Silent Diagnostics Check (Dry-Run)**:
  ```bash
  echo -e "4\n5" | ./setup_googooli.sh
  ```

### 2. Launch Commands (per variant)
* **Obsidian-Agy Gateway**:
  ```bash
  cd implementations/obsidian-agy && source .googooli/venv/bin/activate && bash .googooli/scripts/run_gateway.sh
  ```
* **OpenClaw Agent**:
  ```bash
  cd implementations/openclaw && source venv/bin/activate && PYTHONPATH=. python3 src/run_telegram.py
  ```
* **Free Claude Proxy**:
  ```bash
  cd implementations/free-claude && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8082
  ```

---

## 🛠️ Tool compatibility & Schema Guidelines

### 1. Extending OpenClaw Agent Tools
If the user asks you to add a new system or network capability to the OpenClaw / Free Claude agent:
1. **Define the tool schema** in `implementations/openclaw/src/tools.py` under the `TOOLS_SCHEMA` list (OpenAI/Nvidia NIM compatible format).
2. **Write the execution logic** in `implementations/openclaw/src/tools.py`.
3. **Map the tool dispatch** in `execute_tool(name, arguments)`.

*Schema Example:*
```python
{
    "type": "function",
    "function": {
        "name": "your_tool_name",
        "description": "Describe what the tool does clearly.",
        "parameters": {
            "type": "object",
            "properties": {
                "param_name": {
                    "type": "string",
                    "description": "Description of parameter."
                }
            },
            "required": ["param_name"]
        }
    }
}
```

### 2. Extending Obsidian-Agy Gateway Tools
The Obsidian-Agy gateway uses local shell executables or subprocesses to interact with the environment:
* Helper scripts are stored under `implementations/obsidian-agy/.googooli/scripts/`.
* When writing or calling scripts, make sure paths are constructed dynamically using the `VAULT_ROOT` variable (`os.path.dirname(BASE_DIR)`) instead of absolute home paths.

---

## ⚠️ Critical Constraints & Safety Rules
* **Never commit secrets**: Check that `.env` is listed in `.gitignore` and do not print active API keys in files.
* **Keep paths relative**: Do not write hardcoded absolute paths (like `/home/farhad/` or `/home/mamdaliof/`) inside the codebase. Use python's `os.path` utilities to resolve roots.
* **Python Compatibility**: Keep all code compatible with Python `3.12+`. Do not use modules that restrict operation below Python `3.12`.
