import re

def clean_output(text):
    if not text: return ""
    text = re.sub(r'\[ExtensionManager\].*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'\[ERROR\] \[ImportProcessor\].*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'Discarding invalid hook.*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'\(node:\d+\) \[DEP0190\].*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'Ripgrep is not available.*?\n', '', text)
    text = re.sub(r'Warning: True color.*?\n', '', text)
    text = re.sub(r'Loaded cached credentials\.\n', '', text)
    text = re.sub(r'Obsidian vault connected.*?\n', '', text)
    text = re.sub(r'RAG index updated.*?\n', '', text)
    text = re.sub(r'\[Thought:.*?\]', '', text)
    text = re.sub(r'/caveman \w+', '', text)
    return text.strip()

test_val = """Obsidian vault connected: /home/mamdaliof/Documents/GitHub/mamdaliof-obsidian (147 notes)
RAG index updated: 26 chunks indexed
[ExtensionManager] Error loading agent...
Hello! How can I help you?
"""
print(f"CLEANED: '{clean_output(test_val)}'")
