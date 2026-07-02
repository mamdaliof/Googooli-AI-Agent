# Googooli Agent Specification

This document conceptualizes the architecture, behavior, and environment configurations of the **Googooli** AI assistant. It serves as a central reference for maintaining and developing Googooli's features across local and server environments.

---

## 1. Executive Summary & Purpose

**Googooli** is a personalized AI developer assistant and knowledge engineer designed specifically for Farhad Hoseyni. Its primary purpose is to manage, index, search, and tutor notes, research papers, software projects, and ideas stored inside the Obsidian vault. It interfaces with the vault directly and through external integrations such as NotebookLM and a Telegram gateway.

---

## 2. System Architecture

Googooli operates through three core layers:
1. **User Interface / Gateway**: Interacted with locally via terminal commands or remotely via the Telegram Bot.
2. **Orchestration / CLI**: Executes commands, processes natural language queries, manages context window constraints, and spawns isolated sub-agents.
3. **Vault & External Storage**: Interacts with the Obsidian vault files (Markdown, attachments) and synchronizes with external NotebookLM notebooks.

```mermaid
graph TD
    User([Farhad]) -->|Terminal CLI| AntigravityCLI[Antigravity CLI]
    User -->|Telegram Message| TelegramBot[Telegram bot / Gateway]
    TelegramBot -->|Local Command Proxy| AntigravityCLI
    
    AntigravityCLI -->|Git Sync Hooks| GitRepo[Git Repository]
    AntigravityCLI -->|RAG / File Tools| ObsidianVault[(Obsidian Vault)]
    AntigravityCLI -->|Notebook Sync| NotebookLM[NotebookLM API]
    
    subgraph Personal PC (mamdaliof)
        TerminalCLI[Local Mode]
    end
    
    subgraph Server (Production)
        SystemdService[Googooli systemd Daemon] --> TelegramBot
    end
```

---

## 3. Core Features & Workflows

### A. Deep Ingestion Pipeline (`/ingest`)
* **Trigger**: Executed when files are placed in `00-Inbox/`.
* **Behavior**:
  - Scan `00-Inbox/` for files/subdirectories.
  - Group files inside subdirectories (processed as single tasks) and root files (processed independently).
  - Spawn isolated `@generalist` sub-agents per task unit to minimize context length.
  - Scan `02-Projects/` to check if files belong to an existing project.
  - If project-related: sync/update the matching NotebookLM notebook with the new files.
  - If not project-related: create a target project or learning folder, initialize a NotebookLM notebook, and upload heavy files sequentially.
  - Extract references (YouTube, GitHub, web links), run web research, audit technical gaps/loops, and flag "Persistent Blind Spots".
  - Distill knowledge notes to `03-Knowledge/papers/<slug>.md` or merge/append into project overviews.
  - Move images/attachments to a local `attachments/` folder and rewrite internal links using AST parsing.
  - Clean up the inbox by archiving source files to `00-Inbox/.bin/`.

### B. Interactive Tutor (`/tutor`)
* **Trigger**: `/tutor <topic>`, `"start learning session for <topic>"`, `"help me learn <topic>"`.
* **Behavior**:
  - Locate or create target folder `05-Learning/<topic>/`.
  - Scan vault with `obsidian_rag_query` for related knowledge notes/projects.
  - Update or create a NotebookLM notebook for the topic and upload resources sequentially.
  - Generate/update a structural summary as a hidden `_agent-context.md` file.
  - Conduct Q&A utilizing NotebookLM, falling back to vault RAG for cross-connections.
  - Track comprehension by reading `<topic>-synthesis.md` and applying Socratic critiques.
  - Consolidate synthesis notes back into project/knowledge files.
  - Format recall questions using Obsidian Spaced Repetition syntax (`Question :: Answer`).
  - Update MOCs and clean up notebooks/attachments.

### C. Development SOPs (`/dev`, `/brainstorm`, `/project`)
* **Project Loader (`/project <name>`)**: Loads `_overview.md` and reads the last 5-10 entries of `_dev-log.md` without context bloat.
* **Brainstorm Protocol (`/brainstorm`)**: A 6-step protocol (Listen -> Diverge -> Critique -> Document) with strict Devil's Advocate constraints (must output risk flags).
* **Code Development SOP (`/dev <feature>`)**: Architectural modeling -> complexity tradeoffs matrix (`ask_question` in interactive mode, auto-evaluation in autonomous mode) -> typings/implementation -> branch note creation (`02-Projects/<name>/branches/<feature-name>.md`) -> atomic `_dev-log.md` updates -> git commit.

---

## 4. CLI Transition (Legacy Gemini CLI -> Modern Antigravity CLI)

Googooli is transitioning from using the legacy `gemini` CLI tool to the modern `antigravity` CLI tool. This transition requires updating all command proxy invocations.

### Command Invocation Mapping

| Legacy Gemini CLI Command | Modern Antigravity CLI Command |
|---|---|
| `gemini --approval-mode auto_edit` | `antigravity run` / `antigravity exec` |
| `gemini --allowed-tools <tools>` | Tool permissions are managed natively via dynamic sandbox profiles |
| `gemini --resume latest` | Managed automatically by Antigravity session control |
| `gemini -p "<prompt>"` | `antigravity -p "<prompt>"` |
| `gemini -m <model>` | `antigravity -m <model>` |

### Codebase Modifications
1. **`telegram_gateway.py`**:
   - Update the `run_gemini` helper function to execute `antigravity` CLI commands instead of `gemini`.
   - Update regex cleaners in `clean_output` to strip Antigravity runtime logs instead of legacy `[ExtensionManager]` or Node.js trace noise.
2. **Automation Scripts**:
   - Verify all scripts in `.googooli/scripts/` call `antigravity` where applicable.

---

## 5. Runtime & Environment Configurations

To support development and production execution, the Telegram gateway operates under conditional environments:

### Personal PC (`mamdaliof` / Farhad's local system)
* **Telegram Bot Daemon**: Keep **OFF** by default to prevent port/polling conflicts and avoid unwanted remote access during local workspace editing.
* **Development Mode**: Run the bot script manually (`python3 .googooli/scripts/telegram_gateway.py`) only when actively testing or writing code for the gateway.

### Server (Production / Remote Server)
* **Telegram Bot Daemon**: Keep **ON** continuously.
* **Service Management**: Run as a persistent service via systemd (`googooli.service`) configured as a user-level unit.
* **Git Synchronization**: The service relies on `pre_sync.sh` and `post_sync.sh` hooks to pull vault changes prior to request execution and push updates back to git repository afterward.

---

## 6. Development Conductor Tracks

The Conductor framework maintains the following active development tracks for Googooli:

1. **`track:spec` (Googooli Specification)**: Manage, refine, and update this specification file to align with newly requested features.
2. **`track:cli-migration` (Antigravity CLI Transition)**: Perform the translation of script execution parameters and gateway runner commands to use the Antigravity CLI globally.
3. **`track:gateway` (Telegram Gateway Server)**: Configure systemd user services, paths, auto-restart capabilities, and connection check protocols.
4. **`track:ingest` (Ingest Pipeline)**: Refine multi-agent inbox parsing, NotebookLM synchronizations, and RAG index updates.
5. **`track:tutor` (Interactive Tutor)**: Refine Socratic Q&A tutoring sessions and spaced repetition flashcard generation logic.
6. **`track:dev-sops` (Development SOPs)**: Align project loaders, codebase templates, brainstorming states, and automated branching logs.

---

## 7. Custom Python Helper Scripts

To simplify agent tool invocations, optimize context windows, and prevent errors, several utility scripts are registered in `.googooli/scripts/`:

### A. Inbox Scanner (`inbox_scanner.py`)
* **Path**: [inbox_scanner.py](file:///home/mamdaliof/Documents/GitHub/mamdaliof-obsidian/.googooli/scripts/inbox_scanner.py)
* **Usage**: `python3 .googooli/scripts/inbox_scanner.py`
* **Purpose**: Scans `00-Inbox/` and groups subdirectories/files into discrete JSON task items to be processed by isolated sub-agents.

### B. Image Relocation & Rewriter (`image_rewriter.py`)
* **Path**: [image_rewriter.py](file:///home/mamdaliof/Documents/GitHub/mamdaliof-obsidian/.googooli/scripts/image_rewriter.py)
* **Usage**: `python3 .googooli/scripts/image_rewriter.py <note_path> [source_inbox_dir]`
* **Purpose**: Parses markdown files for local image links, copies the source files into a local `attachments/` folder relative to the note's final location, and rewrites the image links inside the markdown file to point to the new location.

### C. Map of Content Linker (`moc_linker.py`)
* **Path**: [moc_linker.py](file:///home/mamdaliof/Documents/GitHub/mamdaliof-obsidian/.googooli/scripts/moc_linker.py)
* **Usage**: `python3 .googooli/scripts/moc_linker.py <moc_path> <note_path> <category_heading> [note_title]`
* **Purpose**: Automatically appends a link to a newly created note under a specified section/heading in a parent Map of Content (MOC) index file.

### D. Spaced Repetition Flashcard Formatter (`flashcard_formatter.py`)
* **Path**: [flashcard_formatter.py](file:///home/mamdaliof/Documents/GitHub/mamdaliof-obsidian/.googooli/scripts/flashcard_formatter.py)
* **Usage**: `python3 .googooli/scripts/flashcard_formatter.py <note_path>`
* **Purpose**: Scans a note for bullet-list Q&A entries and reformats them into double-colon (`::`) syntax cards for the Obsidian Spaced Repetition plugin.

### E. Project Context Loader (`project_context_loader.py`)
* **Path**: [project_context_loader.py](file:///home/mamdaliof/Documents/GitHub/mamdaliof-obsidian/.googooli/scripts/project_context_loader.py)
* **Usage**: `python3 .googooli/scripts/project_context_loader.py <project_name> [max_log_entries]`
* **Purpose**: Completely reads a project's `_overview.md` and extracts only the last N entries of `_dev-log.md` to feed core context to the developer agent without bloating the context window.

