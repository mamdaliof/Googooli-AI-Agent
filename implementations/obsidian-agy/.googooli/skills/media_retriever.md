# 🎵 Media Retriever Skill

Dedicated tools for finding, downloading, and delivering assets to Farhad.

## Tools

### find_and_deliver_asset
Finds an asset (image/music) on the web and prepares it for Telegram delivery.

**Arguments:**
- `query` (string): The search query (e.g., "jazz music mp3 direct link").
- `file_name` (string): Target local name (e.g., "song.mp3").

**Workflow:**
1. Use `google_web_search` to find a direct download URL.
   - **Smart Search Instruction:** Search for keywords like 'index of', 'direct link', 'raw', or 'cdn' to find non-HTML media targets. Ensure the link points directly to a binary file (.mp3, .jpg, .png) and not an HTML landing page.
2. Use `run_shell_command` with `curl -L` to save to `00-Inbox/temp/<file_name>`.
3. Output: `ACTION_SEND_FILE: /home/mamdaliof/Documents/GitHub/mamdaliof-obsidian/00-Inbox/temp/<file_name>`
