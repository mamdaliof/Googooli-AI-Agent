# 🤖 Googooli Telegram Bot Commands & Features

This document describes the interface, commands, and predefined quick buttons available in the Googooli Telegram gateway bot. It serves as a user manual and developer reference for interacting with Googooli.

---

## 📱 Interactive Bottom Menu (Quick Buttons)

The bot features a persistent custom keyboard at the bottom of the chat view for executing predefined functions:

| Button | Action / Command | Description |
| :--- | :--- | :--- |
| **📊 Project Status** | Local Scan | Reads the root `TODO.md` active projects section and lists all folders in `02-Projects/`. |
| **📑 Tonight's Papers** | DB & Vault Query | Reads the learning queue from `TODO.md` and queries the research database for accepted, unprocessed papers. |
| **🎯 Select Model** | `/model` | Opens an inline menu to select the Gemini model (e.g. Gemini 3.5 Flash, 3.1 Pro, etc.). |
| **🔬 Diagnostics** | `/diagnose_research` | Runs the `check_dependencies.sh` script to verify environment stability. |
| **🧹 Reset Session** | `/clear` or `/reset` | Resets the conversation session, deletes temp files, and clears history baseline. |

---

## ⌨️ Telegram Slash Commands

You can type these commands in the chat at any time:

### `/start`
- **Purpose**: Welcomes the user and restores the quick-access bottom menu.

### `/clear` or `/reset`
- **Purpose**: Cleans the active conversation state.
- **Details**: Deletes the local session ID (`config/session_id`) and clears the history isolation baseline file (`config/raw_history`).

### `/model`
- **Purpose**: Triggers the model selection panel.
- **Details**: Lets you dynamically switch the backend LLM used for processing queries.

### `/diagnose_research`
- **Purpose**: Runs a local dependency audit.
- **Details**: Returns system reports on python library versions, SerpAPI/Tavily configurations, and database accessibility.

### `/research <project_name>`
- **Purpose**: Initiates manual background research for a project.
- **Details**: Spawns a background `research_assistant.py --manual` subprocess to search for and compile literature relevant to the project name.

### `/get_report_summary <project_name>`
- **Purpose**: Fetches a concise summary of a project's research report.
- **Details**: Extracts key queries, top reference links, and implementation overview from the project's `Research-Report.md`.

### `/get_report_full <project_name>`
- **Purpose**: Returns the full contents of the project's research report.
- **Details**: Transmits the entire markdown report (split into chunks if longer than 4000 characters).

---

## 📥 File Upload Options

When you upload a file (document, photo, audio, video, or voice note):

1. **Confirmation Prompt**:
   - The bot caches the binary file and asks: `"Do you want to save it to the vault?"`
   - Buttons: `[Save to Vault]` and `[Do Not Save]`.
2. **Directory Selection**:
   - If you select `Save to Vault`, it presents directory choices:
     - `[Inbox Temp (00-Inbox/temp/)]` (saves to the default temp inbox folder).
     - `[Custom directory...]` (sends a `ForceReply` asking for a folder path relative to the vault root).
3. **Execution**:
   - Once the save decision is finalized, any caption or prompt attached to the file is executed by the agent. If you chose "Do Not Save", the prompt still runs, but the file is not written to your Obsidian vault.
