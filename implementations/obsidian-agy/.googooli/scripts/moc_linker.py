#!/usr/bin/env python3
import os
import sys

def link_to_moc(moc_path, note_path, category_heading, note_title=None):
    """
    Appends a link to `note_path` in the specified `category_heading` section
    of the Map of Content (MOC) note at `moc_path`.
    """
    if not os.path.exists(moc_path):
        print(f"Error: MOC file not found: {moc_path}")
        sys.exit(1)
    if not os.path.exists(note_path):
        print(f"Error: Target note file not found: {note_path}")
        sys.exit(1)

    # Resolve paths relative to vault root
    vault_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    rel_note_path = os.path.relpath(note_path, start=vault_dir)

    # Use filename as title if not provided
    if not note_title:
        note_title = os.path.splitext(os.path.basename(note_path))[0].replace("-", " ").title()

    # Read MOC content
    with open(moc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    target_heading = category_heading.strip().lower()
    heading_index = -1

    for i, line in enumerate(lines):
        if line.strip().startswith("##") and target_heading in line.lower():
            heading_index = i
            break

    if heading_index == -1:
        print(f"⚠️ Warning: Could not locate heading '{category_heading}' in MOC. Appending to end of file.")
        new_link_line = f"- [[{rel_note_path}|{note_title}]]\n"
        lines.append("\n" + new_link_line)
    else:
        # Find insertion index (insert after last list item under this heading, before next heading)
        insert_index = heading_index + 1
        while insert_index < len(lines):
            next_line = lines[insert_index].strip()
            # If we hit another heading, we insert right before it
            if next_line.startswith("##"):
                break
            # Increment to insert after existing list items
            insert_index += 1

        new_link_line = f"- [[{rel_note_path}|{note_title}]]\n"
        lines.insert(insert_index, new_link_line)

    # Write back
    with open(moc_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Successfully added link to MOC: {moc_path} -> {rel_note_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 moc_linker.py <moc_path> <note_path> <category_heading> [note_title]")
        sys.exit(1)

    moc = sys.argv[1]
    note = sys.argv[2]
    category = sys.argv[3]
    title = sys.argv[4] if len(sys.argv) > 4 else None
    
    link_to_moc(moc, note, category, title)
