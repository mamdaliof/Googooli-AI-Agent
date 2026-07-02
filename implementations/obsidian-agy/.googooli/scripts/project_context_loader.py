#!/usr/bin/env python3
import os
import sys

def load_project_context(project_name, max_log_entries=5):
    """
    Locates the project folder in '02-Projects/', reads the full '_overview.md'
    and extracts exactly the last `max_log_entries` from '_dev-log.md'.
    This avoids context window bloating.
    """
    vault_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_dir = os.path.join(vault_dir, "02-Projects", project_name)

    if not os.path.exists(project_dir) or not os.path.isdir(project_dir):
        print(f"Error: Project directory not found: {project_dir}")
        sys.exit(1)

    overview_path = os.path.join(project_dir, "_overview.md")
    dev_log_path = os.path.join(project_dir, "_dev-log.md")

    # 1. Load Overview
    overview_content = ""
    if os.path.exists(overview_path):
        with open(overview_path, "r", encoding="utf-8") as f:
            overview_content = f.read()
    else:
        overview_content = f"# {project_name.title()}\n(No _overview.md found)"

    # 2. Parse Dev Log
    log_entries = []
    if os.path.exists(dev_log_path):
        with open(dev_log_path, "r", encoding="utf-8") as f:
            dev_log_content = f.read()

        # Split content by heading ##
        parts = dev_log_content.split("\n## ")
        if parts:
            # First part is metadata, subsequent parts are logs
            metadata = parts[0]
            entries = parts[1:]
            
            # Select last N entries
            selected_entries = entries[-max_log_entries:]
            log_entries_str = "\n## ".join(selected_entries)
            log_content = f"{metadata}\n## {log_entries_str}"
        else:
            log_content = dev_log_content
    else:
        log_content = "(No _dev-log.md found)"

    print("=== PROJECT OVERVIEW ===")
    print(overview_content)
    print("\n=== RECENT DEV LOGS ===")
    print(log_content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 project_context_loader.py <project_name> [max_log_entries]")
        sys.exit(1)

    proj = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    load_project_context(proj, count)
