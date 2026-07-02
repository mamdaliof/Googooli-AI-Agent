import re
import html
import markdown2

def md_to_tg_html(text):
    if not text: return ""
    text = re.sub(r'\[\[(.*?)\]\]', r'<b>\1</b>', text)
    raw_html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables"])
    raw_html = re.sub(r'<h\d>(.*?)</h\d>', r'<b>\1</b>', raw_html)
    raw_html = re.sub(r'<div class="codehilite"><pre>', '<pre>', raw_html)
    raw_html = re.sub(r'</pre></div>', '</pre>', raw_html)
    allowed_tags = ['b', 'i', 'u', 's', 'code', 'pre', 'a']
    raw_html = re.sub(r'<li>', '• ', raw_html)
    raw_html = re.sub(r'</li>', '\n', raw_html)
    
    def strip_unsupported(match):
        tag_content = match.group(1)
        tag_name = tag_content.split()[0].lower().strip('/')
        return match.group(0) if tag_name in allowed_tags else ""
    
    raw_html = re.sub(r'<(/?.*?)>', strip_unsupported, raw_html)
    raw_html = html.unescape(raw_html)
    raw_html = html.escape(raw_html)
    
    for tag in allowed_tags:
        raw_html = raw_html.replace(f'&lt;{tag}&gt;', f'<{tag}>')
        raw_html = raw_html.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
        if tag == 'a': raw_html = re.sub(r'&lt;a\s+(.*?)&gt;', r'<a \1>', raw_html)
    return raw_html.strip()

test_input = """# Header
This is **bold** and [[link]].
* list item 1
* list item 2

```python
print("hello")
```
"""
print(f"INPUT:\n{test_input}")
print(f"OUTPUT:\n{md_to_tg_html(test_input)}")
