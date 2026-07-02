import os
import subprocess
import requests
import logging
from typing import Dict, Any, List

def run_shell_command(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30.0)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    except Exception as e:
        return f"Error executing command: {e}"

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str) -> str:
    try:
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def list_directory(path: str) -> str:
    try:
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"

def web_fetch(url: str) -> str:
    try:
        response = requests.get(url, timeout=10.0)
        response.raise_for_status()
        return response.text[:10000]
    except Exception as e:
        return f"Error fetching URL: {e}"

def google_web_search(query: str) -> str:
    try:
        from src.config import Config
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(project_dir, ".env")
        config = Config(env_path)
        tavily_key = config.tavily_api_key

        if tavily_key:
            tavily_url = "https://api.tavily.com/search"
            payload = {
                "api_key": tavily_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": False
            }
            response = requests.post(tavily_url, json=payload, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            output = []
            for i, result in enumerate(data.get("results", [])):
                title = result.get("title", "No Title")
                url = result.get("url", "")
                snippet = result.get("content", "")
                output.append(f"Result #{i+1}:\nTitle: {title}\nURL: {url}\nSnippet: {snippet}\n")
            return "\n".join(output) if output else "No search results found via Tavily."

        # Fallback to DuckDuckGo Lite
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        import urllib.parse
        import html as html_parser
        import re
        
        url = "https://lite.duckduckgo.com/lite/"
        payload = {"q": query}
        response = requests.post(url, headers=headers, data=payload, timeout=10.0)
        response.raise_for_status()
        
        body = response.text
        results = re.findall(r'href=[\'\"]([^\'\"]+)[\'\"]\s+class=[\'\"]result-link[\'\"]>([^<]+)</a>', body)
        snippets = re.findall(r'class=[\'\"]result-snippet[\'\"]>\s*(.*?)\s*</td>', body, re.DOTALL)
        
        output = []
        for i in range(min(len(results), len(snippets))):
            link = results[i][0]
            title = results[i][1]
            snippet = snippets[i].strip()
            
            snippet_clean = re.sub(r'<[^>]+>', '', snippet)
            snippet_clean = html_parser.unescape(snippet_clean)
            title_clean = html_parser.unescape(title)
            
            clean_url = urllib.parse.unquote(link)
            if "uddg=" in clean_url:
                clean_url = clean_url.split("uddg=")[1].split("&")[0]
                
            output.append(f"Result #{i+1}:\nTitle: {title_clean}\nURL: {clean_url}\nSnippet: {snippet_clean}\n")
            
        return "\n".join(output) if output else "No search results found."
    except Exception as e:
        return f"Search error: {e}"

def download_file(url: str, destination_path: str) -> str:
    resolved_path = None
    try:
        if not destination_path or os.path.isdir(destination_path):
            import urllib.parse
            filename = os.path.basename(urllib.parse.urlparse(url).path)
            if not filename:
                filename = "downloaded_file"
            destination_path = os.path.join(destination_path or ".", filename)
        else:
            generic_names = {"cvpr_paper.pdf", "arxiv_paper.pdf", "paper.pdf", "downloaded_file.pdf", "file.pdf", "downloaded_file", "paper.jpg", "image.jpg", "horse.jpg"}
            basename = os.path.basename(destination_path)
            if basename.lower() in generic_names:
                import urllib.parse
                url_filename = os.path.basename(urllib.parse.urlparse(url).path)
                if url_filename:
                    if "." not in url_filename and "." in basename:
                        ext = basename.split(".")[-1]
                        url_filename = f"{url_filename}.{ext}"
                    destination_path = os.path.join(os.path.dirname(destination_path), url_filename)
        
        resolved_path = destination_path
        if os.path.exists(resolved_path):
            try:
                os.remove(resolved_path)
            except Exception:
                pass

        dir_name = os.path.dirname(resolved_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, stream=True, timeout=30.0)
        response.raise_for_status()
        
        with open(resolved_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # Validate PDF content if the destination path ends with .pdf
        if resolved_path.lower().endswith(".pdf"):
            if os.path.exists(resolved_path):
                with open(resolved_path, "rb") as test_f:
                    header = test_f.read(4)
                if header != b"%PDF":
                    with open(resolved_path, "r", errors="ignore") as test_f:
                        snippet = test_f.read(300)
                    try:
                        os.remove(resolved_path)
                    except Exception:
                        pass
                    return f"Error: The downloaded URL did not return a valid PDF. It returned HTML/text content instead. Header: {header}. Snippet: {snippet.strip()}. Please search for the direct PDF URL."
                    
        return f"Successfully downloaded file to {resolved_path}"
    except Exception as e:
        if resolved_path and os.path.exists(resolved_path):
            try:
                os.remove(resolved_path)
            except Exception:
                pass
        return f"Error downloading file: {e}. The file was deleted to prevent corruption."

def _find_command(name: str, fallback_path: str) -> str:
    import shutil
    resolved = shutil.which(name)
    if resolved:
        return resolved
    if os.path.exists(fallback_path):
        return fallback_path
    return name

NOTEBOOKLM_CMD = _find_command("notebooklm", "/root/.local/bin/notebooklm")
C7_CMD = _find_command("c7", "/usr/local/bin/c7")

def notebooklm_list() -> str:
    try:
        result = subprocess.run([NOTEBOOKLM_CMD, "list"], capture_output=True, text=True, timeout=30.0)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    except Exception as e:
        return f"Error executing notebooklm list: {e}"

def notebooklm_create(title: str) -> str:
    try:
        result = subprocess.run([NOTEBOOKLM_CMD, "create", title], capture_output=True, text=True, timeout=30.0)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    except Exception as e:
        return f"Error creating notebooklm: {e}"

def notebooklm_ask(notebook_id: str, question: str) -> str:
    try:
        result = subprocess.run([NOTEBOOKLM_CMD, "ask", question, "--notebook", notebook_id], capture_output=True, text=True, timeout=60.0)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    except Exception as e:
        return f"Error asking notebooklm: {e}"

def notebooklm_add_source(notebook_id: str, source_path_or_url: str, source_type: str) -> str:
    try:
        result = subprocess.run([NOTEBOOKLM_CMD, "source", "add", source_path_or_url, "--notebook", notebook_id, "--type", source_type], capture_output=True, text=True, timeout=60.0)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    except Exception as e:
        return f"Error adding source to notebooklm: {e}"

def context7_query(project_identifier: str, query: str) -> str:
    try:
        result = subprocess.run([C7_CMD, project_identifier, query], capture_output=True, text=True, timeout=30.0)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    except Exception as e:
        return f"Error querying context7: {e}"

def context7_search(term: str) -> str:
    try:
        result = subprocess.run([C7_CMD, "search", term], capture_output=True, text=True, timeout=30.0)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    except Exception as e:
        return f"Error searching context7: {e}"

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Execute a shell command on the host server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to run."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of a file on disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite content to a file on disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path."},
                    "content": {"type": "string", "description": "Content to write."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders inside a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch HTML content from a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to load."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "google_web_search",
            "description": "Search the web for a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notebooklm_list",
            "description": "List all Google NotebookLM notebooks.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notebooklm_create",
            "description": "Create a new Google NotebookLM notebook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the notebook."}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notebooklm_ask",
            "description": "Ask a question to a Google NotebookLM notebook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notebook_id": {"type": "string", "description": "Notebook ID or partial ID."},
                    "question": {"type": "string", "description": "The question to ask."}
                },
                "required": ["notebook_id", "question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notebooklm_add_source",
            "description": "Add a source to a Google NotebookLM notebook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notebook_id": {"type": "string", "description": "Notebook ID or partial ID."},
                    "source_path_or_url": {"type": "string", "description": "Local file path or URL."},
                    "source_type": {
                        "type": "string",
                        "description": "Type of source.",
                        "enum": ["file", "url", "youtube", "text"]
                    }
                },
                "required": ["notebook_id", "source_path_or_url", "source_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "context7_query",
            "description": "Query the Context7 API for documentation/context of a project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_identifier": {"type": "string", "description": "Project path (e.g. org/repo) or unique name (e.g. repo)."},
                    "query": {"type": "string", "description": "The topic or question to query."}
                },
                "required": ["project_identifier", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "context7_search",
            "description": "Search for projects and paths in the Context7 API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Search term."}
                },
                "required": ["term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_file",
            "description": "Download a file (like a PDF paper, document, or image) from a URL to a local destination path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to download."},
                    "destination_path": {"type": "string", "description": "Local path (file path or directory path) to save the downloaded file."}
                },
                "required": ["url", "destination_path"]
            }
        }
    }
]

def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    if name == "run_shell_command":
        return run_shell_command(arguments.get("command", ""))
    elif name == "read_file":
        return read_file(arguments.get("path", ""))
    elif name == "write_file":
        return write_file(arguments.get("path", ""), arguments.get("content", ""))
    elif name == "list_directory":
        return list_directory(arguments.get("path", ""))
    elif name == "web_fetch":
        return web_fetch(arguments.get("url", ""))
    elif name == "google_web_search":
        return google_web_search(arguments.get("query", ""))
    elif name == "download_file":
        return download_file(arguments.get("url", ""), arguments.get("destination_path", ""))
    elif name == "notebooklm_list":
        return notebooklm_list()
    elif name == "notebooklm_create":
        return notebooklm_create(arguments.get("title", ""))
    elif name == "notebooklm_ask":
        return notebooklm_ask(arguments.get("notebook_id", ""), arguments.get("question", ""))
    elif name == "notebooklm_add_source":
        return notebooklm_add_source(
            arguments.get("notebook_id", ""),
            arguments.get("source_path_or_url", ""),
            arguments.get("source_type", "")
        )
    elif name == "context7_query":
        return context7_query(arguments.get("project_identifier", ""), arguments.get("query", ""))
    elif name == "context7_search":
        return context7_search(arguments.get("term", ""))
    else:
        return f"Unknown tool: {name}"
