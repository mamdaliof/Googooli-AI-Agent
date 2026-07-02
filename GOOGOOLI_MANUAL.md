# 📖 Googooli Assistant: Operation Manual & Command Reference

This guide explains the inner workings, workflows, and command reference of the **Googooli Assistant** to help you understand, operate, and extend it.

---

## 🧠 How Googooli Works

Googooli operates as an orchestration agent that links user interfaces (like Telegram) to system tools, local notes databases, and large language models.

```
                  ┌──────────────────────────────┐
                  │      Telegram Bot User       │
                  └──────────────┬───────────────┘
                                 │ Text, Files, Buttons
                                 ▼
                  ┌──────────────────────────────┐
                  │   telegram_gateway.py        │
                  └──────────────┬───────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼ (Variant 1)         ▼ (Variant 2)         ▼ (Variant 3)
     ┌───────────┐         ┌───────────┐         ┌───────────┐
     │  agy CLI  │         │ Nvidia NIM│         │Claude Code│
     │ Sandbox   │         │ Agent     │         │ Proxy     │
     └─────┬─────┘         └─────┬─────┘         └─────┬─────┘
           │                     │                     │
           ▼                     ▼                     ▼
     ┌───────────┐         ┌───────────┐         ┌───────────┐
     │ Obsidian  │         │ System    │         │ Local     │
     │ Vault RAG │         │ Shell /   │         │ Terminal  │
     │ MCP Tools │         │NotebookLM │         │ Workspace │
     └───────────┘         └───────────┘         └───────────┘
```

### 1. The Core Loop
* The bot waits for messages from authorized chat IDs.
* When a text message arrives, it is processed as a task unit.
* In the **Obsidian-Agy** variant, the prompt is passed to the Antigravity sandbox (`agy --dangerously-skip-permissions --print prompt`).
* In the **OpenClaw** and **Free Claude** variants, the prompt is sent directly to Nvidia NIM for chat completion, which dynamically triggers tools defined in `tools.py`.

### 2. File Upload & Caching Mechanism
When a user uploads a document, photo, voice note, or video:
1. **Caching**: The bot intercepts the raw binary data and caches it locally.
2. **Approval Prompt**: The bot asks: *"Do you want to save it to the vault?"* with inline buttons: `[Save to Vault]` and `[Do Not Save]`.
3. **Directory Routing**:
   * If `Save to Vault` is chosen, the bot prompts with folder presets (e.g., `00-Inbox/temp/`) or requests a custom path.
   * If `Do Not Save` is chosen, the prompt is executed against the temporary cache, but the file is not written to the Obsidian vault directory.

### 3. State & Research database
Googooli tracks scientific papers, study guides, and topics using a local SQLite database (`research_state.db`):
* **Phase 1**: Checks literature indexes (via SemanticsScholar/Tavily) and proposes paper candidates.
* **Phase 2**: Updates the learning queues and downloads PDFs into the vault.
* **Weekly Autotuning**: Analyzes past read notes and proposes adding or removing focus keywords.

---

## ⌨️ Bot Interface & Commands

The gateway provides both interactive keyboard buttons and slash commands.

### 📱 Bottom Keyboard Menu
* **📊 Project Status**: Scans the root `TODO.md` file's active projects section and lists all current directories under `02-Projects/`.
* **📑 Tonight's Papers**: Queries the database for accepted research papers that have not been processed yet.
* **🎯 Select Model**: Switch the backend LLM (Gemini 3.5 Flash, 3.1 Pro, etc.) dynamically.
* **🔬 Diagnostics**: Runs a check on local environments and libraries.
* **🧹 Reset Session**: Clears chat memory and isolation baselines.

### ⌨️ Telegram Slash Commands
* `/start` - Re-initializes keyboard menus.
* `/clear` or `/reset` - Clears conversation history and logs.
* `/model` - Opens an inline menu to choose a specific LLM.
* `/diagnose_research` - Runs local diagnostic verification scripts.
* `/research <topic>` - Spawns a background literature research subprocess to compile data on the specified topic.
* `/get_report_summary <project>` - Extracts key links and abstracts from a project's `Research-Report.md`.
* `/get_report_full <project>` - Returns the entire research report.
