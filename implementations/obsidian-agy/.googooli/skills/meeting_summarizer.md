# 🤝 Meeting Summaries Skill

Automates recording, summarizing, and organizing meeting information in the vault.

## Command: `/meeting`

**Goal:** Process raw meeting data, generate a structured note using the meeting template, and save it to the `02-Projects/meetings/` directory.

### Workflow

1.  **Context Gathering:**
    *   Ask Farhad for the meeting title/topic if not provided.
    *   Extract members, agenda, and key discussion points from the input.
2.  **Note Creation:**
    *   Use the template: `Settings/templates/13 - Meeting/13.1 - Meeting.md`.
    *   File naming: `02-Projects/meetings/YYYY-MM-DD - <Meeting Title>.md`.
    *   Populate YAML frontmatter and sections (Agenda, Goals, Discussion, Action Items).
3.  **Cross-linking:**
    *   If the meeting is related to an active project, link it in the project's `_dev-log.md` and the meeting note itself.
    *   Run `obsidian_rag_query` to find related notes and add them to the `## Related` section.
4.  **Finalization:**
    *   Save the note.
    *   Report completion and path to Farhad.

## Guidelines

*   **Terse Mode:** Use `/caveman lite` for the summary content.
*   **Zero Orphan:** Ensure at least one link to a project or the daily note.
*   **Action Items:** Highlight action items in the response so Farhad sees them immediately.
