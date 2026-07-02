# Googooli Tracks Implementation Plans

This document provides the step-by-step implementation plans for each of the five pending development tracks of the Googooli AI Assistant.

---

## 1. Track: `track:cli-migration` (Antigravity CLI Transition)

### Goal
Migrate the assistant's runtime executor from the legacy `gemini` CLI tool to the new `antigravity` CLI tool globally across all environments.

### Tasks
- [ ] **Analyze CLI Differences**: Map parameter conversions (e.g., how sandbox profiles, dynamic rules, and session controls behave in `antigravity`).
- [ ] **Update Gateway Invocations**:
  - Modify `.googooli/scripts/telegram_gateway.py` to call `antigravity` instead of `gemini`.
  - Adapt parameters: map legacy `--approval-mode` and `--allowed-tools` to the new runner execution arguments.
  - **Fallback Scenario**: Implement a fallback mechanism. If `antigravity` CLI execution fails (e.g., command not found or sandbox initialization error), fall back to running the legacy `gemini` CLI, but prepend a warning banner (`⚠️ Warning: Running in legacy Gemini fallback mode`) in the Telegram bot chat to alert the user.
- [ ] **Refine Output Cleaners**:
  - Update the `clean_output` regex pattern in `telegram_gateway.py` to handle `antigravity` logs, sandbox warning headers, and session indicators.
  - *Purpose*: Removing internal CLI startup trace lines, sandbox warnings, and Node.js stderr noise so that only clean Markdown text is sent back to Farhad in the Telegram chat window.
- [ ] **Verify Migration**:
  - Execute test runs of the modified bot gateway locally and check the responses.

---

## 2. Track: `track:gateway` (Telegram Gateway Server)

### Goal
Configure the Telegram bot daemon for production server usage and set up correct user-level environment execution limits on the personal PC.

### Tasks
- [ ] **Configure run script**:
  - Update `.googooli/scripts/run_gateway.sh` to remove all `/root/` and `fnm` dependencies.
  - Set `PATH` explicitly to target `/usr/bin` and `/usr/local/bin`.
  - Use `/usr/bin/python3` explicitly to bypass Conda active environments.
- [ ] **Create Systemd Service**:
  - Write `googooli.service` in `~/.config/systemd/user/`.
  - Point working directory to your local Obsidian vault root folder.
- [ ] **Implement Environment Control**:
  - Modify `telegram_gateway.py` or startup scripts to inspect the hostname.
  - On personal PC (`mamdaliof`), prevent systemd auto-start (keep service stopped/disabled by default).
  - On the server host, ensure the service is enabled and started automatically.
- [ ] **Check service stability**:
  - Load the service using `systemctl --user daemon-reload`.
  - Verify start/stop behavior and inspect logs using journalctl.

---

## 3. Track: `track:ingest` (Ingest Pipeline)

### Goal
Refine the multi-agent inbox ingestion pipeline (`/ingest`) to parse resources, update NotebookLM libraries, and clean up directory structures.

### Tasks
- [ ] **Inbox Scanner & Grouper**:
  - Script directory grouping for subdirectories under `00-Inbox/`.
  - Ensure root files are mapped to single isolated tasks.
- [ ] **Sub-Agent Orchestrator**:
  - Implement task queue processing where each segment is handled by a freshly spawned `@generalist` sub-agent.
- [ ] **NotebookLM Queue Controller**:
  - Build sequential upload limits to prevent API rate-limits when processing large files.
- [ ] **Image Relocation & AST Link Rewriter**:
  - Implement a python script to parse Markdown AST, extract image references, move target files to local `attachments/`, and update paths to relative references.
- [ ] **Inbox Archiver**:
  - Move fully ingested raw files to `00-Inbox/.bin/`.

---

## 4. Track: `track:tutor` (Interactive Tutor)

### Goal
Optimize the active learning engine (`/tutor`) to provide cross-linked learning materials, check user comprehension, and generate recall tasks.

### Tasks
- [ ] **Cross-Reference Scanner**:
  - Script a title/tag scanning system that queries the vault for existing knowledge nodes related to the active learning topic.
- [ ] **Active Socratic Proctor**:
  - Implement routines that read `<topic>-synthesis.md` and cross-analyze against source summaries (`_agent-context.md`) to point out comprehension gaps.
- [ ] **Spaced Repetition Generator**:
  - Parse notes to automatically format key concepts as spaced-repetition cards utilizing the double-colon syntax (`Question :: Answer`).
- [ ] **MOC Updating Hooks**:
  - Add hooks to insert newly finalized concept notes into parent Map of Content (MOC) index files automatically.

---

## 5. Track: `track:dev-sops` (Development SOPs)

### Goal
Establish strict, automated workflows for writing code, brainstorming features, loading context, and committing changes.

### Tasks
- [ ] **Context Loader (`/project`)**:
  - Create a script that reads `_overview.md` completely and extracts exactly the last 5-10 logs of `_dev-log.md` without loading full file sizes.
- [ ] **Brainstorm state-machine (`/brainstorm`)**:
  - Script a 6-step state tracker with interactive prompts (`ask_question` checkpoints).
  - Codify the Devil's Advocate warning rule.
- [ ] **Git Pre/Post Hook Integrations**:
  - Enforce `pre_sync.sh` (fetch & merge origin main) and `post_sync.sh` (automatic add, commit with sync message, and push) on each agent execution safely.
