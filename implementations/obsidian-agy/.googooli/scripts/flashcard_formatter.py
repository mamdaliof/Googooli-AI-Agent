#!/usr/bin/env python3
import os
import re
import sys

def format_flashcards(note_path):
    """
    Parses a note and formats list-based Q&As into spaced repetition syntax.
    Example:
      - Question?
        - Answer.
      Becomes:
      - Question? :: Answer.
    """
    if not os.path.exists(note_path):
        print(f"Error: Note file not found: {note_path}")
        sys.exit(1)

    with open(note_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match:
    # - Question line ending in '?'
    # - Followed by indented line containing the answer
    qa_pattern = re.compile(r'(^[ \t]*- [^\n\?]+\?)\s*\n[ \t]+- ([^\n]+)', re.MULTILINE)
    
    def replacer(match):
        question = match.group(1).rstrip()
        answer = match.group(2).strip()
        # Ensure it formats using the double-colon syntax
        return f"{question} :: {answer}"

    updated_content = qa_pattern.sub(replacer, content)
    
    if updated_content != content:
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Successfully formatted flashcards in: {note_path}")
    else:
        print("No flashcards needed reformatting.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 flashcard_formatter.py <note_path>")
        sys.exit(1)
    
    target_note = sys.argv[1]
    format_flashcards(target_note)
