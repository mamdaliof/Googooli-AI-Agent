#!/usr/bin/env python3
import os
import re
import shutil
import sys

def rewrite_images(note_path, source_dir=None):
    """
    Parses a markdown note to extract image references, copies referenced images
    to a local 'attachments/' folder relative to the note, and rewrites the
    image links in the markdown note to point to the new location.
    """
    if not os.path.exists(note_path):
        print(f"Error: Note file not found: {note_path}")
        sys.exit(1)

    note_dir = os.path.dirname(os.path.abspath(note_path))
    attachments_dir = os.path.join(note_dir, "attachments")
    
    with open(note_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find Obsidian style images: ![[image.png]] or ![[image.png|caption]]
    obsidian_pattern = re.compile(r'!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
    # Find Markdown style images: ![caption](image.png)
    markdown_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    updated_content = content
    modified = False

    # Collect unique image files
    images_to_move = []

    # 1. Parse Obsidian patterns
    for match in obsidian_pattern.finditer(content):
        img_name = match.group(1).strip()
        images_to_move.append((match.group(0), img_name, True))

    # 2. Parse standard Markdown patterns
    for match in markdown_pattern.finditer(content):
        caption = match.group(1)
        img_path = match.group(2).strip()
        # Skip web urls
        if img_path.startswith("http://") or img_path.startswith("https://"):
            continue
        images_to_move.append((match.group(0), img_path, False))

    if not images_to_move:
        print("No local image references found in note.")
        return

    # Ensure attachments dir exists
    os.makedirs(attachments_dir, exist_ok=True)

    for original_link, img_ref, is_obsidian in images_to_move:
        # Locate the source image file
        img_filename = os.path.basename(img_ref)
        source_path = None

        # Search locations:
        # 1. Absolute/Relative direct path
        # 2. Look in note's directory
        # 3. Look in specified source_dir (inbox/temp folder etc)
        # 4. Look in vault root
        possible_paths = [
            os.path.abspath(img_ref),
            os.path.join(note_dir, img_ref),
            os.path.join(note_dir, img_filename),
        ]
        if source_dir:
            possible_paths.append(os.path.join(source_dir, img_ref))
            possible_paths.append(os.path.join(source_dir, img_filename))
            possible_paths.append(os.path.join(source_dir, "attachments", img_filename))

        # Add vault root search
        vault_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        possible_paths.append(os.path.join(vault_dir, img_ref))
        possible_paths.append(os.path.join(vault_dir, "attachments", img_filename))

        for path in possible_paths:
            if os.path.exists(path) and os.path.isfile(path):
                source_path = path
                break

        if not source_path:
            print(f"⚠️ Warning: Could not locate source file for: {img_ref}")
            continue

        # Target file path
        dest_filename = img_filename.replace(" ", "_")
        dest_path = os.path.join(attachments_dir, dest_filename)

        # Copy the image file
        try:
            shutil.copy2(source_path, dest_path)
            print(f"Copied image: {source_path} -> {dest_path}")
            
            # Rewrite link to standard relative path: attachments/filename
            relative_dest = f"attachments/{dest_filename}"
            if is_obsidian:
                new_link = f"![[{relative_dest}]]"
            else:
                new_link = f"![{caption}]({relative_dest})"
                
            updated_content = updated_content.replace(original_link, new_link)
            modified = True
        except Exception as e:
            print(f"❌ Error copying {img_ref}: {str(e)}")

    if modified:
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Successfully updated note: {note_path}")
    else:
        print("Note links were not modified.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 image_rewriter.py <note_path> [source_dir]")
        sys.exit(1)
    
    target_note = sys.argv[1]
    search_dir = sys.argv[2] if len(sys.argv) > 2 else None
    rewrite_images(target_note, search_dir)
