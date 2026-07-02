---
name: interactive-tutor
description: >
  Manages an interactive learning session for a specific topic under 05-Learning/. 
  Finds related vault notes/projects, syncs/updates existing notebooks, uploads materials sequentially,
  and refines existing files using isolated subagents to prevent context bloating.
  Trigger: "start learning session for <topic>", "/tutor <topic>", "help me learn <topic>"
---

# Interactive Tutor Workflow

## File Naming Conventions
- **LLM Conversations (PDFs/Text)**: `llm-chat-<source>-<date>.pdf` (e.g., `llm-chat-gpt4-20260525.pdf`)
- **User Synthesis Note**: `<topic>-synthesis.md` (Farhad's active notes)
- **Agent Hidden Summary**: `_agent-context.md` (Your internal reference)

## Phase 1: Initialization & Cross-Reference Discovery
1. **Target Folder**: Locate `05-Learning/<topic>/`. Create if missing.
2. **Cross-Reference Scan**:
   * Before uploading or creating resources, scan the vault using title search and `obsidian_rag_query` to identify related existing knowledge notes (under `03-Knowledge/`) or project directories (under `02-Projects/`).
   * Locate any existing NotebookLM notebooks associated with these related concepts (note: notebooks do not require a strict `Learn-` prefix and may match topic/project names directly, e.g., "Medical Image Processing", "XAI").
3. **Task Segmentation & Orchestration**:
   * Discover all files and folders in `05-Learning/<topic>/`.
   * Group all files within subdirectories to be processed/tutored together.
   * Process root files within the topic directory separately.
   * Spawn a fresh `@generalist` sub-agent via `invoke_subagent` for each processing unit. This keeps context sizes minimal and prevents unrelated files from bleeding context into each other.
4. **NotebookLM Synchronization**:
   * If related notebooks exist, update them by uploading the new files sequentially (never parallelize uploads to avoid rate-limiting).
   * If no matching notebooks exist, create a new notebook matching the topic name directly and upload the heavy files sequentially.
5. **Agent Summary**: Query NotebookLM to generate/update a structural summary of the materials. Save this as `05-Learning/<topic>/_agent-context.md` (keep hidden from user).
6. **User Synthesis File**: Ensure `05-Learning/<topic>/<topic>-synthesis.md` exists for Farhad's active notes.

## Phase 2: Active Tutoring (Sub-agent Execution)
1. **Q&A**: Answer user questions utilizing the specific NotebookLM notebook. Fall back to vault RAG (`obsidian_rag_query`) for cross-connecting with other topics.
2. **Tracking & Alignment**: Read changes to `<topic>-synthesis.md` to track the user's comprehension.
3. **Socratic Check**: Point out discrepancies or gaps between the user's synthesis notes and the source material.

## Phase 3: Finalization & Refinement (Sub-agent Execution)
1. **Deep Ingest**: Trigger the Multi-Agent Deep Ingest Pipeline (`/ingest` logic) on the `05-Learning/<topic>/` folder.
2. **Flashcard Formatting**: You can automatically format bullet-pointed questions and answers into spaced repetition double-colon (`::`) syntax by running:
   `python3 .googooli/scripts/flashcard_formatter.py <note_path>`
3. **Refinement of Existing Knowledge**:
   * Consolidate `<topic>-synthesis.md` and `_agent-context.md` back into the identified related project or knowledge files directly, updating and refining existing documents instead of only creating new isolated files.
   * Update or create permanent atomic notes in `03-Knowledge/` or `05-Learning/`.
4. **MOC Update**: Automatically update parent Map of Content (MOC) index files with links to newly created concept files by running:
   `python3 .googooli/scripts/moc_linker.py <moc_path> <note_path> <category_heading> [note_title]`
5. **Cleanup**: Archive or clean up the Notebooks. Move raw chat logs and source PDFs to `.bin/` or `attachments/` relative to the updated/created notes.