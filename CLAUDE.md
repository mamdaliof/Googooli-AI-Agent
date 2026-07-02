# Claude Code Instructions (CLAUDE.md)

Refer to [AGENTS.md](AGENTS.md) for full details on project architecture, environment setup, diagnostics commands, and custom tool mapping.

---

## Quick Reference Commands

* **Run Setup/Diagnostics**: `./setup_googooli.sh` (or `echo -e "4\n5" | ./setup_googooli.sh` for silent dry-run)
* **Obsidian-Agy Gateway**: `cd implementations/obsidian-agy && source .googooli/venv/bin/activate && bash .googooli/scripts/run_gateway.sh`
* **OpenClaw Agent**: `cd implementations/openclaw && source venv/bin/activate && PYTHONPATH=. python3 src/run_telegram.py`
* **Free Claude Proxy**: `cd implementations/free-claude && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8082`

## Guidelines

1. **Python version**: Keep code compatible with Python `>=3.12`.
2. **Paths**: Never use absolute home paths. Always build paths dynamically relative to `VAULT_ROOT` or package roots.
3. **Secrets**: Do not hardcode API keys. Save them in `.env`.
