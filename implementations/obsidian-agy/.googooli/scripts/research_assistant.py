#!/usr/bin/env python3
"""Googooli Research Assistant Engine.
Handles:
- Phase 1 (--phase1): 1:00 AM Search & Suggestion Loop (arXiv, PaperCash, last30days, and Conference scraping via Tavily).
- Phase 2 (--phase2): 6:00 AM Processing Loop (Deeps Q&As on dedicated NotebookLM workspaces, vault note generation, and backlinks).
- Weekly Autotuning (--weekly): Weekly communications analytics proposing keyword updates with Telegram approval.
- Manual Project Research (--manual <project_name>): Scans READMEs/TODOs, searches web for solutions, queries NotebookLM, and writes a detailed report inside the project directory.
"""

import os
import sys
import json
import sqlite3
import random
import re
import time
import subprocess
import urllib.request
import telebot
import html
from telebot import types
from datetime import datetime
import zoneinfo


def get_netherlands_time():
    """Returns the current time in the Europe/Amsterdam timezone."""
    tz = zoneinfo.ZoneInfo("Europe/Amsterdam")
    return datetime.now(tz)


# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT_ROOT = os.path.dirname(BASE_DIR)
ENV_PATH = os.path.join(BASE_DIR, "config/.env")
CONFIG_PATH = os.path.join(BASE_DIR, "config/research-assistant-config.json")
INTERESTS_PATH = os.path.join(VAULT_ROOT, "07-Tools/Googooli-Research-Interests.md")
DB_PATH = os.path.join(BASE_DIR, "data/research_state.db")
TEMP_DIR = os.path.join(BASE_DIR, "data/temp")

# Load environment
ENV = {}
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                try:
                    k, v = line.strip().split("=", 1)
                    ENV[k] = v.replace('"', "").replace("'", "")
                    os.environ[k] = ENV[k]
                except ValueError:
                    continue

bot = telebot.TeleBot(ENV.get("GOOGOOLI_TELEGRAM_TOKEN", ""))
CHAT_ID = ENV.get("GOOGOOLI_CHAT_ID", "")


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def parse_interests():
    """Extracts keywords and conferences from Googooli-Research-Interests.md."""
    keywords = []
    conferences = []
    if os.path.exists(INTERESTS_PATH):
        with open(INTERESTS_PATH, "r") as f:
            content = f.read()

        # Extract keywords from bullet list under section 4
        kw_section = re.search(r"## 4\. Current Target Keywords.*?(?:\n\n|\Z)", content, re.DOTALL)
        if kw_section:
            keywords = re.findall(r"-\s*`([^`]+)`", kw_section.group(0))

        # Extract conferences from section 2
        conf_section = re.search(r"### Conferences.*?(?:###|\Z)", content, re.DOTALL)
        if conf_section:
            conferences = re.findall(r"\[\[(.*?)\]\]", conf_section.group(0))

    cfg = load_config()
    if not keywords:
        keywords = cfg.get("fields_of_interest", ["computer vision", "AI", "robotics"])
    if not conferences:
        conferences = cfg.get("conferences", ["CVPR", "ICLR", "ICCV", "ICRA", "IROS", "CASE"])

    return keywords, conferences


def run_papercash_search(query):
    """Runs PaperCash search in subprocess. Filters out MDPI papers."""
    script_path = os.path.join(BASE_DIR, "tools/PaperCash/scripts/papercash.py")
    cmd = [sys.executable, script_path, "search", query, "--limit", "15", "--emit", "json"]
    papers = []
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        json_match = re.search(r"\{.*\}", res.stdout, re.DOTALL)
        if json_match:
            raw_papers = json.loads(json_match.group(0)).get("papers", [])
            for p in raw_papers:
                # MDPI Filter
                url = p.get("url", "")
                title = p.get("title", "")
                if "mdpi.com" in url.lower() or "mdpi" in title.lower():
                    continue
                papers.append(p)
    except Exception as e:
        print(f"⚠️ PaperCash search failed for '{query}': {e}")
    return papers


def run_last30days_raw_search(query, search_sources=None):
    """Runs last30days-skill and returns the raw parsed JSON response dictionary."""
    paths = [
        os.path.join(BASE_DIR, "tools/last30days-skill/skills/last30days/scripts/last30days.py"),
        "/root/.gemini/config/plugins/last30days-skill/skills/last30days/scripts/last30days.py",
        "/root/.gemini/extensions/last30days-skill/skills/last30days/scripts/last30days.py"
    ]
    script_path = None
    for p in paths:
        if os.path.exists(p):
            script_path = p
            break
            
    if not script_path:
        print("⚠️ last30days.py script not found in any location.")
        return {}

    py_bin = "python3"
    for py in ["python3.12", "python3.13", "python3.14", "python3"]:
        try:
            res = subprocess.run([py, "-c", "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)"], capture_output=True, timeout=5)
            if res.returncode == 0:
                py_bin = py
                break
        except Exception:
            continue

    cmd = [py_bin, script_path, "--quick", "--emit", "json"]
    if search_sources:
        cmd.extend(["--search", search_sources])
    cmd.append(query)

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        json_match = re.search(r"\{.*\}", res.stdout, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            print(f"⚠️ last30days search did not return valid JSON. stdout: {res.stdout[:500]}")
    except Exception as e:
        print(f"⚠️ last30days search execution failed for '{query}': {e}")
    return {}


def run_last30days_search(query):
    """Runs last30days-skill search in subprocess. Filters out MDPI papers."""
    data = run_last30days_raw_search(query)
    items = []
    if not data:
        return items
    raw_items = data.get("items", [])
    for item in raw_items:
        # MDPI Filter
        url = item.get("url", "")
        title = item.get("title", "")
        if "mdpi.com" in url.lower() or "mdpi" in title.lower():
            continue
        items.append(item)
    return items


def run_conference_search(conf, keywords):
    """Searches official conference site using Tavily for keywords."""
    domains = {
        "CVPR": "openaccess.thecvf.com",
        "ICCV": "openaccess.thecvf.com",
        "ICLR": "openreview.net",
        "ICRA": "ieeexplore.ieee.org",
        "IROS": "ieeexplore.ieee.org",
        "CASE": "ieeexplore.ieee.org"
    }
    domain = domains.get(conf, "")
    results = []
    
    tav_key = os.getenv("TAVILY_API_KEY")
    if not tav_key:
        return []
        
    # Search from the most recent years
    current_year = int(get_netherlands_time().strftime("%Y"))
    for year in range(current_year, current_year - 2, -1):
        selected_kws = random.sample(keywords, min(2, len(keywords))) if keywords else []
        for kw in selected_kws:
            query = f"site:{domain} {conf} {year} {kw} pdf"
            try:
                from tavily import TavilyClient
                tav_client = TavilyClient(api_key=tav_key)
                search_res = tav_client.search(query, max_results=3)
                for r in search_res.get("results", []):
                    title = r.get("title", "")
                    url = r.get("url", "")
                    snippet = r.get("content", "")
                    if "mdpi.com" in url.lower() or "mdpi" in title.lower():
                        continue
                    if url.endswith(".pdf") or "pdf" in url.lower() or "openaccess" in url:
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "source": conf,
                            "venue": f"{conf} {year}",
                            "citation_count": 0,
                            "final_score": 20.0,
                            "relevance_score": 0.9,
                            "year": year
                        })
            except Exception as e:
                print(f"⚠️ Tavily conference search failed for '{query}': {e}")
    results = sorted(results, key=lambda x: x.get("year", 0), reverse=True)
    return results


def run_google_scholar_search(query):
    """Searches Google Scholar using SerpAPI (if configured) or falls back to Tavily site:scholar.google.com."""
    papers = []
    # 1. Try SerpAPI if SERPAPI_API_KEY is present
    serp_key = os.getenv("SERPAPI_API_KEY")
    if serp_key:
        try:
            import urllib.request
            import urllib.parse
            encoded_q = urllib.parse.quote(query)
            url = f"https://serpapi.com/search?engine=google_scholar&q={encoded_q}&api_key={serp_key}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
                for result in data.get("organic_results", []):
                    title = result.get("title", "")
                    link = result.get("link", "")
                    snippet = result.get("snippet", "")
                    pub_info = result.get("publication_info", {})
                    # MDPI filter
                    if "mdpi.com" in link.lower() or "mdpi" in title.lower():
                        continue
                    # Try to extract year from publication info
                    year = 0
                    summary = pub_info.get("summary", "")
                    year_match = re.search(r"\b(19|20)\d{2}\b", summary)
                    if year_match:
                        year = int(year_match.group(0))
                    
                    papers.append({
                        "title": title,
                        "url": link,
                        "snippet": snippet,
                        "source": "Google Scholar",
                        "venue": summary,
                        "citation_count": result.get("inline_links", {}).get("cited_by", {}).get("total", 0),
                        "year": year
                    })
        except Exception as e:
            print(f"⚠️ SerpAPI Google Scholar search failed: {e}")

    # 2. Fallback to Tavily site:scholar.google.com
    if not papers:
        tav_key = os.getenv("TAVILY_API_KEY")
        if tav_key:
            try:
                from tavily import TavilyClient
                tav_client = TavilyClient(api_key=tav_key)
                search_res = tav_client.search(f"site:scholar.google.com {query}", max_results=5)
                for r in search_res.get("results", []):
                    title = r.get("title", "")
                    link = r.get("url", "")
                    snippet = r.get("content", "")
                    # MDPI filter
                    if "mdpi.com" in link.lower() or "mdpi" in title.lower():
                        continue
                    papers.append({
                        "title": title,
                        "url": link,
                        "snippet": snippet,
                        "source": "Google Scholar (Tavily)",
                        "venue": "Google Scholar",
                        "citation_count": 0,
                        "year": int(get_netherlands_time().strftime("%Y"))
                    })
            except Exception as e:
                print(f"⚠️ Tavily Google Scholar search fallback failed: {e}")
    return papers


def get_notebook_id(title="Googooli Research"):
    """Gets or creates the NotebookLM workspace ID."""
    try:
        res = subprocess.run(["notebooklm", "list", "--json"], capture_output=True, text=True)
        data = json.loads(res.stdout)
        for nb in data.get("notebooks", []):
            if nb.get("title") == title:
                return nb.get("id")

        res_create = subprocess.run(["notebooklm", "create", title, "--json"], capture_output=True, text=True)
        created_data = json.loads(res_create.stdout)
        return created_data.get("id") or created_data.get("notebook", {}).get("id")
    except Exception as e:
        print(f"⚠️ Failed to get/create NotebookLM: {e}")
    return None


def download_arxiv_pdf(url):
    """Downloads arXiv PDF to temporary directory and returns local path."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    pdf_match = re.search(r"arxiv\.org/abs/(\d+\.\d+)", url)
    if not pdf_match:
        pdf_match = re.search(r"arxiv\.org/pdf/(\d+\.\d+)", url)
    if not pdf_match:
        return None

    arxiv_id = pdf_match.group(1)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    local_path = os.path.join(TEMP_DIR, f"{arxiv_id}.pdf")

    try:
        print(f"📥 Downloading PDF: {pdf_url} -> {local_path}")
        urllib.request.urlretrieve(pdf_url, local_path)
        return local_path
    except Exception as e:
        print(f"⚠️ arXiv PDF download failed: {e}")
    return None


def download_arxiv_pdf_by_title(title):
    """Searches arXiv by title, downloads PDF if found, and returns local path."""
    import urllib.request
    import urllib.parse
    import xml.etree.ElementTree as ET
    
    print(f"🔍 ArXiv fallback: searching by title: '{title}'")
    try:
        query_url = 'http://export.arxiv.org/api/query?search_query=' + urllib.parse.quote('ti:"' + title + '"') + '&max_results=1'
        req = urllib.request.Request(query_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        if entry is not None:
            for link in entry.findall('atom:link', ns):
                if link.attrib.get('title') == 'pdf' or link.attrib.get('type') == 'application/pdf':
                    pdf_url = link.attrib.get('href')
                    if pdf_url:
                        if not pdf_url.endswith('.pdf'):
                            pdf_url += '.pdf'
                        os.makedirs(TEMP_DIR, exist_ok=True)
                        clean_t = re.sub(r'[^\w\s-]', '', title).strip()[:50].strip()
                        local_path = os.path.join(TEMP_DIR, f"{clean_t}.pdf")
                        print(f"📥 Downloading fallback PDF: {pdf_url} -> {local_path}")
                        urllib.request.urlretrieve(pdf_url, local_path)
                        return local_path
    except Exception as e:
        print(f"⚠️ ArXiv title search/download failed: {e}")
    return None


def run_notebooklm_ask(question, notebook_id, resolve_references=False, use_personality=True):
    """Asks NotebookLM a question with --json output and extracts the clean answer.
    Retries up to 3 times on failure. Optionally resolves and appends a References section."""
    if use_personality:
        question += (
            "\n\n[STYLE GUIDELINE: Respond using 'Caveman Lite' style. "
            "Keep descriptions and content concise, omit conversational fluff or filler, "
            "but preserve standard grammar, proper verbs, and readable formatting. "
            "Do not include polite greetings or conversational introductions/conclusions.]"
        )
    source_map = {}
    if resolve_references:
        try:
            list_res = subprocess.run(["notebooklm", "source", "list", "--notebook", notebook_id, "--json"], capture_output=True, text=True)
            if list_res.returncode == 0:
                sources_data = json.loads(list_res.stdout)
                for src in sources_data.get("sources", []):
                    source_map[src.get("id")] = src.get("title")
        except Exception:
            pass

    for attempt in range(1, 4):
        try:
            cmd = ["notebooklm", "ask", question, "--notebook", notebook_id, "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                answer = data.get("answer") or data.get("response", {}).get("answer") or res.stdout.strip()
                
                # Append references if requested
                refs = data.get("references", [])
                if resolve_references and refs and source_map:
                    ref_lines = []
                    seen_numbers = set()
                    for ref in refs:
                        num = ref.get("citation_number")
                        if num and num not in seen_numbers:
                            seen_numbers.add(num)
                            src_id = ref.get("source_id")
                            src_title = source_map.get(src_id, "Unknown Source")
                            cited_text = ref.get("cited_text", "").strip().replace("\n", " ")
                            if len(cited_text) > 80:
                                cited_text = cited_text[:80] + "..."
                            ref_lines.append(f"[{num}] **{src_title}**: \"{cited_text}\"")
                    
                    if ref_lines:
                        # Sort numerically by citation number
                        ref_lines.sort(key=lambda x: int(re.search(r"^\[(\d+)\]", x).group(1)))
                        answer += "\n\n---\n\n### 📑 References\n" + "\n".join(ref_lines)
                
                return answer.strip()
            else:
                print(f"⚠️ NotebookLM ask returned non-zero code {res.returncode} on attempt {attempt}: {res.stderr}")
                time.sleep(2)
        except Exception as e:
            print(f"⚠️ NotebookLM ask failed on attempt {attempt}: {e}")
            time.sleep(2)
    return ""


def free_youtube_search(query):
    """Searches YouTube and returns the top 2 video links using raw scraping."""
    import urllib.request, urllib.parse, re
    urls = []
    try:
        q = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={q}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            matches = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
            seen = set()
            for m in matches:
                if m not in seen:
                    seen.add(m)
                    urls.append(f"https://www.youtube.com/watch?v={m}")
                if len(urls) >= 2:
                    break
    except Exception as e:
        print(f"⚠️ Free YouTube search failed: {e}")
    return urls


def fetch_arxiv_metadata(arxiv_id):
    """Fetches title and description for an arXiv paper using its ID via arXiv API."""
    import urllib.request, xml.etree.ElementTree as ET
    try:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('atom:entry', ns)
            if entry is not None:
                title = entry.find('atom:title', ns).text.strip().replace("\n", " ")
                summary = entry.find('atom:summary', ns).text.strip().replace("\n", " ")
                published = entry.find('atom:published', ns).text
                year = int(published[:4]) if published else 0
                return {
                    "title": title,
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "snippet": summary,
                    "source": "arXiv",
                    "venue": f"arXiv {year}",
                    "citation_count": 0,
                    "year": year
                }
    except Exception as e:
        print(f"⚠️ Failed to fetch arXiv metadata for {arxiv_id}: {e}")
    return None


def run_social_paper_search(query):
    """Searches Reddit, Twitter, and YouTube for papers matching query using last30days and Tavily."""
    candidates = []
    seen_ids = set()
    
    # 1. Use last30days-skill for direct social searches
    print(f"📡 Querying last30days-skill for social discussions on '{query}'...")
    social_data = run_last30days_raw_search(query, "reddit,x,youtube")
    if social_data:
        raw_items = social_data.get("items", [])
        for item in raw_items:
            item_source = item.get("source", "").lower()
            source_label = "Reddit"
            if any(k in item_source for k in ["x", "twitter", "bird", "xurl", "xai"]):
                source_label = "Twitter"
            elif "youtube" in item_source:
                source_label = "YouTube"
                
            text_to_scan = f"{item.get('url', '')} {item.get('title', '')} {item.get('description', '')} {item.get('selftext', '')}"
            matches = re.findall(r"arxiv\.org/(abs|pdf)/(\d+\.\d+)", text_to_scan)
            for m in matches:
                arxiv_id = m[1]
                if arxiv_id not in seen_ids:
                    seen_ids.add(arxiv_id)
                    meta = fetch_arxiv_metadata(arxiv_id)
                    if meta:
                        meta["source"] = source_label
                        candidates.append(meta)
                        print(f"  -> Found paper on {source_label} via last30days: '{meta['title']}'")

    # 2. Fallback / Supplement using Tavily if API key is available
    tav_key = os.getenv("TAVILY_API_KEY")
    if tav_key:
        print("📡 Querying Tavily for supplemental social discussions...")
        try:
            from tavily import TavilyClient
            tav_client = TavilyClient(api_key=tav_key)
            
            social_queries = [
                f"site:arxiv.org {query} reddit",
                f"site:arxiv.org {query} twitter",
                f"site:arxiv.org {query} youtube"
            ]
            
            for sq in social_queries:
                try:
                    res = tav_client.search(sq, max_results=5)
                    for r in res.get("results", []):
                        url = r.get("url", "")
                        match = re.search(r"arxiv\.org/(abs|pdf)/(\d+\.\d+)", url)
                        if match:
                            arxiv_id = match.group(2)
                            if arxiv_id not in seen_ids:
                                seen_ids.add(arxiv_id)
                                meta = fetch_arxiv_metadata(arxiv_id)
                                if meta:
                                    meta["source"] = "Reddit" if "reddit" in sq else ("Twitter" if "twitter" in sq else "YouTube")
                                    candidates.append(meta)
                                    print(f"  -> Found paper via Tavily: '{meta['title']}'")
                except Exception as e:
                    print(f"⚠️ Tavily social search failed for query '{sq}': {e}")
        except Exception as e:
            print(f"⚠️ Tavily social paper search client init failed: {e}")
            
    return candidates


def check_vault_note_exists(concept):
    """Scans the Obsidian vault to see if a note matching the concept name exists."""
    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if file.lower() == f"{concept.lower()}.md":
                return os.path.join(root, file)
    return None


def analyze_prerequisites(pdf_path, nb_id):
    """Uploads PDF to NotebookLM, extracts summaries and prerequisites."""
    summary = "Unable to extract summary."
    prereqs = []
    if not pdf_path or not nb_id:
        return summary, prereqs

    try:
        res_add = subprocess.run(["notebooklm", "source", "add", pdf_path, "--notebook", nb_id, "--type", "file", "--json"], capture_output=True, text=True)
        src_id = json.loads(res_add.stdout).get("id") or json.loads(res_add.stdout).get("source", {}).get("id")
        if not src_id:
            return summary, prereqs

        subprocess.run(["notebooklm", "source", "wait", src_id, "--notebook", nb_id, "--timeout", "300"], capture_output=True)

        summary = run_notebooklm_ask("Provide a clear 2-sentence summary of this paper.", nb_id, use_personality=True)
        raw_prereqs = run_notebooklm_ask("List 2 to 3 core prerequisite concepts/background topics required to understand this paper. Format as a simple comma-separated list of nouns only (e.g. Graph Neural Networks, Reinforcement Learning).", nb_id, use_personality=False)
        if raw_prereqs:
            prereqs = [p.strip() for p in raw_prereqs.split(",") if p.strip()]

    except Exception as e:
        print(f"⚠️ NotebookLM analysis failed: {e}")

    return summary, prereqs


def evaluate_candidates(candidates, conferences, cursor=None, limit=None, chosen_urls=None):
    """Selects diverse candidates based on non-redundant metrics."""
    if chosen_urls is None:
        chosen_urls = set()
    used_urls = set()
    deduped_candidates = []
    
    suggested_urls = set()
    if cursor:
        try:
            cursor.execute("SELECT url FROM suggestions")
            suggested_urls = {row[0] for row in cursor.fetchall()}
        except Exception as e:
            print(f"⚠️ Failed to query suggested URLs: {e}")

    for c in candidates:
        url = c.get("url", "").lower()
        title = c.get("title", "").lower()
        year = c.get("year", 0)

        # 1. Skip MDPI papers completely
        if "mdpi" in url or "mdpi" in title:
            continue

        # 2. Skip books, chapters, lecture notes, textbook, handbook, encyclopedia, springer
        book_keywords = ["book", "chapter", "lecture notes", "springer", "handbook", "textbook", "encyclopedia"]
        if any(bk in url or bk in title for bk in book_keywords):
            continue

        # 3. Skip older papers (< 2016)
        if year > 0 and year < 2016:
            continue

        if c.get("url") not in used_urls and c.get("url") not in suggested_urls and c.get("url") not in chosen_urls:
            used_urls.add(c.get("url"))
            deduped_candidates.append(c)

    def get_year_weight(c):
        year = c.get("year", 0)
        if year >= 2024:
            return 3000
        elif year >= 2020:
            return 1500
        elif year >= 2016:
            return 500
        return 0

    # 10 Non-redundant metrics
    def rank_recency(c):
        return c.get("year", 0) * 10

    def rank_citation_count(c):
        return c.get("citation_count", 0) + get_year_weight(c)

    def rank_github_stars(c):
        score = 1000 if "github.com" in c.get("url", "") else 0
        return score + get_year_weight(c)

    def rank_keyword_relevance(c):
        return c.get("relevance_score", 0.0) * 100 + get_year_weight(c)

    def rank_hacker_news_score(c):
        score = c.get("final_score", 0.0) if c.get("source") == "hackernews" else 0
        return score + get_year_weight(c)

    def rank_tutorial_completeness(c):
        title = c.get("title", "").lower()
        snippet = c.get("snippet", c.get("description", "")).lower()
        score = 500 if any(w in title or w in snippet for w in ["tutorial", "guide", "walkthrough", "introduction", "how-to", "video"]) else 0
        return score + get_year_weight(c)

    def rank_vault_backlink_density(c):
        title = c.get("title", "").lower()
        score = 0
        for w in ["anomaly", "tracking", "robot", "mri", "segmentation", "u-net", "pick", "place", "factory"]:
            if w in title:
                score += 100
        return score + get_year_weight(c)

    def rank_conference_prestige(c):
        venue = c.get("venue", "").upper()
        score = 0
        for conf in conferences:
            if conf.upper() in venue:
                score = c.get("year", 0)
                break
        return score + get_year_weight(c)

    def rank_huggingface_trending(c):
        score = 500 if "huggingface.co" in c.get("url", "") else 0
        return score + get_year_weight(c)

    def rank_open_access_status(c):
        url = c.get("url", "").lower()
        score = 500 if (url.endswith(".pdf") or "openaccess" in url or "openreview" in url or "arxiv.org" in url) else 0
        return score + get_year_weight(c)

    metric_rankers = [
        ("Recency", rank_recency),
        ("Citation Count", rank_citation_count),
        ("GitHub Stars", rank_github_stars),
        ("Keyword Relevance", rank_keyword_relevance),
        ("Hacker News Score", rank_hacker_news_score),
        ("Tutorial Completeness", rank_tutorial_completeness),
        ("Vault Backlink Density", rank_vault_backlink_density),
        ("Conference Prestige", rank_conference_prestige),
        ("HuggingFace Trending", rank_huggingface_trending),
        ("Open Access Status", rank_open_access_status)
    ]

    selected_set = []
    conference_paper_count = 0

    cfg = load_config()
    if limit is None:
        limit = cfg.get("suggestions_limit", 10)
    randomness = cfg.get("randomness_factor", 0.2)

    for metric_name, ranker in metric_rankers[:limit]:
        # Filter out already chosen candidates and check limits
        available = []
        for c in deduped_candidates:
            if c.get("url") in chosen_urls:
                continue
            
            # Conference Limit Check (max 2)
            is_conf = any(conf.upper() in c.get("venue", "").upper() for conf in conferences)
            if is_conf and conference_paper_count >= 2:
                continue
            available.append(c)

        if not available:
            placeholder = {
                "title": f"Dynamic Placeholder ({metric_name})",
                "url": f"https://placeholder.com/{time.time()}",
                "description": "Dynamic search candidate placeholder.",
                "source": "Placeholder",
                "metric": metric_name
            }
            selected_set.append(placeholder)
            continue

        if random.random() < randomness:
            best = random.choice(available)
            best["metric"] = "Random Exploration"
        else:
            best = max(available, key=ranker)
            best["metric"] = metric_name
        
        # Increment conference count if matched
        if any(conf.upper() in best.get("venue", "").upper() for conf in conferences):
            conference_paper_count += 1
            
        selected_set.append(best)
        chosen_urls.add(best.get("url"))

    return selected_set[:limit]


def phase1_search_loop():
    """Phase 1: 1:00 AM Search Loop."""
    print("🌅 Phase 1: Running 1:00 AM Search Loop...")
    keywords, conferences = parse_interests()

    # Generate 10 search queries dynamically via agy
    print("🧠 Generating search queries using Googooli agent...")
    interests_content = ""
    if os.path.exists(INTERESTS_PATH):
        with open(INTERESTS_PATH, "r") as f:
            interests_content = f.read()

    prompt = f"""You are the Googooli Research Assistant.
Analyze Farhad's research interests, target fields, and current keywords from this file content:
{interests_content}

Generate exactly 10 highly specific, advanced, and trending search queries for research papers.
Requirements:
1. 7 queries must be 'general' search queries (for finding new SOTA papers on arXiv, Google Scholar, etc.).
2. 3 queries must be 'conference' search queries (tailored to find recent publications from CVPR, ICLR, ICCV, ICRA, IROS, CASE).
3. Do NOT make the queries generic. They must be technical, specific, and reflect current SOTA trends.
4. Output MUST be a valid JSON object matching this structure:
{{
  "general": [
    "query 1",
    "query 2",
    ...
  ],
  "conference": [
    "query 8",
    "query 9",
    "query 10"
  ]
}}
Do NOT wrap the output in markdown code blocks. Output ONLY raw JSON.
"""

    general_queries = []
    conference_queries = []
    try:
        res = subprocess.run(["agy", "--print", prompt], capture_output=True, text=True, check=True)
        output = res.stdout.strip()
        if output.startswith("```"):
            output = re.sub(r"^```(?:json)?\n", "", output)
            output = re.sub(r"\n```$", "", output)
        
        data = json.loads(output.strip())
        general_queries = data.get("general", [])
        conference_queries = data.get("conference", [])
        print(f"✅ Dynamically generated {len(general_queries)} general and {len(conference_queries)} conference queries.")
    except Exception as e:
        print(f"⚠️ Query generation failed: {e}. Falling back to default keywords.")
        general_queries = random.sample(keywords, min(7, len(keywords))) if keywords else ["computer vision", "AI", "deep learning"]
        conference_queries = random.sample(keywords, min(3, len(keywords))) if keywords else ["computer vision", "robotics"]

    # 1. Keyword search (arXiv + PaperCash + last30days + Google Scholar + Social)
    general_candidates = []
    for q in general_queries:
        print(f"🔍 Searching general query: {q}")
        general_candidates.extend(run_papercash_search(q))
        general_candidates.extend(run_last30days_search(q))
        general_candidates.extend(run_google_scholar_search(q))
        general_candidates.extend(run_social_paper_search(q))

    # 2. Conference proceedings direct crawl (newest first)
    conference_candidates = []
    selected_confs = random.sample(conferences, min(3, len(conferences))) if conferences else []
    for conf in selected_confs:
        print(f"🔍 Crawling proceedings for conference: {conf}")
        conference_candidates.extend(run_conference_search(conf, conference_queries))

    # Open DB connection earlier to check duplicates in evaluate_candidates
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 3. Select diverse candidates: 5 general search, 3 from favorite conferences
    chosen_urls = set()
    selected_general = evaluate_candidates(general_candidates, conferences, cursor, limit=5, chosen_urls=chosen_urls)
    selected_general = [c for c in selected_general if c.get("source") != "Placeholder"]

    selected_conference = evaluate_candidates(conference_candidates, conferences, cursor, limit=3, chosen_urls=chosen_urls)
    selected_conference = [c for c in selected_conference if c.get("source") != "Placeholder"]

    # Fill remaining conference slots with general candidates if needed to guarantee 8 papers
    needed = 3 - len(selected_conference)
    if needed > 0:
        print(f"⚠️ Only found {len(selected_conference)} conference papers. Backfilling {needed} slots with general candidates...")
        extra_general = evaluate_candidates(general_candidates, conferences, cursor, limit=needed, chosen_urls=chosen_urls)
        extra_general = [c for c in extra_general if c.get("source") != "Placeholder"]
        selected_conference.extend(extra_general)

    selected_candidates = selected_general + selected_conference

    nb_id = get_notebook_id()
    today = get_netherlands_time().strftime("%Y-%m-%d")

    for idx, c in enumerate(selected_candidates, 1):
        title = c.get("title")
        url = c.get("url")
        source = c.get("source", "Web")
        metric = c.get("metric", "General")
        abstract = c.get("abstract") or c.get("snippet") or "No description available."

        pdf_path = download_arxiv_pdf(url)
        if not pdf_path and title:
            pdf_path = download_arxiv_pdf_by_title(title)
        summary, prereqs = analyze_prerequisites(pdf_path, nb_id)
        if not summary or not isinstance(summary, str) or summary.startswith("Unable"):
            summary = abstract
        if not summary:
            summary = "No description available."

        prereq_status = []
        for pr in prereqs:
            path = check_vault_note_exists(pr)
            if path:
                prereq_status.append(f"• 🔗 {pr} (Vault: Found)")
            else:
                prereq_status.append(f"• ❌ {pr} (Vault: MISSING)")

        prereq_text = "\n".join(prereq_status) if prereq_status else "• None identified"

        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

        try:
            cursor.execute("""
            INSERT INTO suggestions (title, url, source, description, prerequisites, metric, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, url, source, summary, json.dumps(prereqs), metric, today))
            conn.commit()
            sug_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM suggestions WHERE url = ?", (url,))
            sug_id = cursor.fetchone()[0]

        # Inline Accept/Reject/Later buttons
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn_yes = types.InlineKeyboardButton("👍 Yes (Accept)", callback_data=f"research_accept:{sug_id}")
        btn_no = types.InlineKeyboardButton("👎 No (Reject)", callback_data=f"research_reject:{sug_id}")
        btn_later = types.InlineKeyboardButton("⏳ Later", callback_data=f"research_later:{sug_id}")
        markup.add(btn_yes, btn_no, btn_later)

        msg_text = (
            f"<b>📌 Research Candidate #{idx}</b>\n"
            f"<b>Title:</b> {html.escape(title or 'Untitled')}\n"
            f"<b>Source:</b> {source} ({metric})\n"
            f"<b>URL:</b> {url}\n\n"
            f"<b>AI Summary:</b>\n{html.escape(summary)}\n\n"
            f"<b>Prerequisite Concept Check:</b>\n{prereq_text}\n\n"
            f"<i>ID: {sug_id}</i>"
        )
        try:
            bot.send_message(CHAT_ID, msg_text, parse_mode="HTML", reply_markup=markup)
            time.sleep(1)
        except Exception as te:
            print(f"⚠️ Failed to send Telegram card: {te}")

    # 4. Fetch up to 3 random "later" suggestions to re-propose
    print("⏳ Querying random 'later' items to re-propose...")
    try:
        cursor.execute("""
        SELECT id, title, url, source, description, prerequisites, metric 
        FROM suggestions 
        WHERE status = 'later'
        ORDER BY RANDOM() LIMIT 3
        """)
        later_items = cursor.fetchall()
        for row in later_items:
            s_id, s_title, s_url, s_source, s_summary, s_prereqs_json, s_metric = row
            
            # Load prerequisites
            try:
                s_prereqs = json.loads(s_prereqs_json) if s_prereqs_json else []
            except Exception:
                s_prereqs = []
                
            s_prereq_status = []
            for pr in s_prereqs:
                path = check_vault_note_exists(pr)
                if path:
                    s_prereq_status.append(f"• 🔗 {pr} (Vault: Found)")
                else:
                    s_prereq_status.append(f"• ❌ {pr} (Vault: MISSING)")

            s_prereq_text = "\n".join(s_prereq_status) if s_prereq_status else "• None identified"

            markup_later = types.InlineKeyboardMarkup(row_width=3)
            btn_yes = types.InlineKeyboardButton("👍 Yes (Accept)", callback_data=f"research_accept:{s_id}")
            btn_no = types.InlineKeyboardButton("👎 No (Reject)", callback_data=f"research_reject:{s_id}")
            btn_later = types.InlineKeyboardButton("⏳ Later", callback_data=f"research_later:{s_id}")
            markup_later.add(btn_yes, btn_no, btn_later)

            msg_text_later = (
                f"<b>⏳ Re-proposed Candidate (from Later stack)</b>\n"
                f"<b>Title:</b> {html.escape(s_title or 'Untitled')}\n"
                f"<b>Source:</b> {s_source} ({s_metric})\n"
                f"<b>URL:</b> {s_url}\n\n"
                f"<b>AI Summary:</b>\n{html.escape(s_summary or 'No description available.')}\n\n"
                f"<b>Prerequisite Concept Check:</b>\n{s_prereq_text}\n\n"
                f"<i>ID: {s_id}</i>"
            )
            try:
                bot.send_message(CHAT_ID, msg_text_later, parse_mode="HTML", reply_markup=markup_later)
                time.sleep(1)
            except Exception as te:
                print(f"⚠️ Failed to send Telegram card for Later item #{s_id}: {te}")
    except Exception as dbe:
        print(f"⚠️ Failed to query Later items from DB: {dbe}")

    conn.close()
    print("✅ Phase 1 complete. Suggestions sent.")


def convert_json_mind_map_to_mermaid(json_path):
    """Reads a mind-map JSON and formats it as a Mermaid flowchart or hierarchical markdown."""
    if not os.path.exists(json_path):
        return "Mind map file not found."
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # If list, wrap
        if isinstance(data, list):
            data = {"children": data}
        
        lines = ["```mermaid", "graph TD"]
        
        # DFS Helper to generate nodes and links
        def traverse(node, parent_id=None, node_counter=[0]):
            node_counter[0] += 1
            curr_id = f"node{node_counter[0]}"
            title = node.get("title", node.get("name", node.get("text", "Node")))
            # Clean title for Mermaid
            clean_title = re.sub(r'[^\w\s-]', '', title).strip()
            lines.append(f'  {curr_id}["{clean_title}"]')
            if parent_id:
                lines.append(f"  {parent_id} --> {curr_id}")
            
            children = node.get("children", node.get("nodes", []))
            for child in children:
                traverse(child, curr_id, node_counter)
        
        traverse(data)
        lines.append("```")
        return "\n".join(lines)
    except Exception as e:
        print(f"⚠️ Mind map parsing failed: {e}")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return f"```json\n{f.read()[:2000]}\n```"
        except:
            return "Failed to parse mind map."


def generate_prerequisite_note_recursive(prereq, paper_nb_id, depth=0):
    """Recursively generates concept notes for prerequisites up to 2 levels deep."""
    if depth > 1: # 2 levels total: depth 0, depth 1
        return None
        
    exists = check_vault_note_exists(prereq)
    if exists:
        return f"- [[{prereq}]] (Existing Vault Note)"
        
    pr_clean = re.sub(r'[^\w\s-]', '', prereq).strip()
    if not pr_clean:
        return None
    pr_note_path = os.path.join(VAULT_ROOT, "05-Learning", f"{pr_clean}.md")
    
    pr_explanation = "Background explanation unavailable."
    sub_prereqs = []
    if paper_nb_id:
        try:
            # 1. Ask for explanation
            pr_explanation = run_notebooklm_ask(f"Explain the prerequisite concept: {prereq} in detail. Provide background context, key formulations, and its role in the field of AI/CV. Do NOT use numerical citations.", paper_nb_id, use_personality=True)
            
            # 2. Ask for sub-prerequisites
            raw_sub = run_notebooklm_ask(f"List 2 fundamental sub-concepts or prerequisite topics required to understand {prereq}. Format as a simple comma-separated list of nouns only. Do NOT use numerical citations.", paper_nb_id, use_personality=False)
            if raw_sub and not raw_sub.startswith("Unable") and "," in raw_sub:
                sub_prereqs = [s.strip() for s in raw_sub.split(",") if s.strip() and s.strip().lower() != prereq.lower()]
        except Exception as e:
            print(f"⚠️ Prerequisite Q&A failed for '{prereq}': {e}")
            
    # Generate sub-prerequisite notes recursively
    sub_links = []
    for sub in sub_prereqs[:2]:
        link_text = generate_prerequisite_note_recursive(sub, paper_nb_id, depth + 1)
        if link_text:
            sub_links.append(link_text)
            
    sub_text = "\n".join(sub_links) if sub_links else "- None identified"
    
    pr_content = f"""# Prerequisite Concept: {prereq}

*Generated as part of study guide at depth {depth}*

---

## 📖 Background & Explanation
{pr_explanation}

---

## 🔗 Sub-Prerequisite Concepts
{sub_text}
"""
    try:
        with open(pr_note_path, "w", encoding="utf-8") as pf:
            pf.write(pr_content)
        print(f"✅ Prerequisite concept note created at depth {depth}: {pr_note_path}")
    except Exception as e:
        print(f"⚠️ Failed to write prerequisite note: {e}")
        
    return f"- [[05-Learning/{pr_clean}|{prereq}]] (Prerequisite Note)"
def link_note_to_daily_note(note_title, note_rel_path, date_str):
    daily_note_dir = os.path.join(VAULT_ROOT, "01-Daily")
    os.makedirs(daily_note_dir, exist_ok=True)
    daily_note_path = os.path.join(daily_note_dir, f"{date_str}.md")
    
    link_content = f"- [[05-Learning/{note_rel_path}/Overview|{note_title}]]"
    heading = "## 🔬 Research Studies"
    
    if os.path.exists(daily_note_path):
        with open(daily_note_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if link already exists
        if link_content in content:
            return
            
        # Append to the heading
        if heading in content:
            new_content = content.replace(heading, f"{heading}\n{link_content}")
        else:
            new_content = content.rstrip() + f"\n\n{heading}\n{link_content}\n"
            
        with open(daily_note_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    else:
        new_content = f"# 📅 Daily Note: {date_str}\n\n{heading}\n{link_content}\n"
        with open(daily_note_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    print(f"✅ Linked paper to daily note: {daily_note_path}")


def update_research_index_note(note_title, note_rel_path, date_str):
    index_path = os.path.join(VAULT_ROOT, "05-Learning", "Googooli-Research-Index.md")
    link_line = f"- **{date_str}**: [[05-Learning/{note_rel_path}/Overview|{note_title}]]"
    
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if link_line in content:
            return
            
        heading = "## 📄 Research Paper Index"
        if heading in content:
            new_content = content.replace(heading, f"{heading}\n{link_line}")
        else:
            new_content = content.rstrip() + f"\n\n{heading}\n{link_line}\n"
            
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    else:
        new_content = f"""# 🗺️ Googooli Research Index

This note aggregates all literature study guides compiled by the Googooli Research Assistant.

## 📄 Research Paper Index
{link_line}
"""
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    print(f"✅ Updated central research index: {index_path}")


def phase2_ingestion_loop():
    """Phase 2: 6:00 AM Processing Loop."""
    print("🌅 Phase 2: Running 6:00 AM Ingestion Loop...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, url, source, description, prerequisites, metric, user_notes 
    FROM suggestions 
    WHERE status = 'accepted' AND processed = 0
    """)
    accepted = cursor.fetchall()

    if not accepted:
        print("No pending accepted suggestions to process.")
        conn.close()
        return

    for sug_id, title, url, source, description, prereqs_json, metric, user_notes in accepted:
        print(f"⚙️ Deep processing paper: {title}")
        prereqs = json.loads(prereqs_json)

        # Deeper web context retrieval (including related papers & youtube/github/hf/social links)
        context_data = ""
        youtube_links = []
        github_links = []
        hf_links = []
        twitter_links = []
        reddit_links = []
        related_papers = []
        related_res = {}

        # 1. Use last30days-skill for social media links extraction
        print(f"📡 Querying last30days-skill for social media links related to '{title}'...")
        social_data = run_last30days_raw_search(title)
        if social_data:
            raw_items = social_data.get("items", [])
            for item in raw_items:
                url = item.get("url", "")
                if not url:
                    continue
                item_source = item.get("source", "").lower()
                if "youtube" in item_source or "youtube.com" in url or "youtu.be" in url:
                    if url not in youtube_links:
                        youtube_links.append(url)
                elif "reddit" in item_source or "reddit.com" in url:
                    if url not in reddit_links:
                        reddit_links.append(url)
                elif "github" in item_source or "github.com" in url:
                    if url not in github_links:
                        github_links.append(url)
                elif "huggingface.co" in url:
                    if url not in hf_links:
                        hf_links.append(url)
                elif any(k in item_source for k in ["x", "twitter", "bird", "xurl", "xai"]) or "twitter.com" in url or "x.com" in url:
                    if url not in twitter_links:
                        twitter_links.append(url)

        # 2. Tavily context/supplement
        tav_key = os.getenv("TAVILY_API_KEY")
        if tav_key:
            print("📡 Querying Tavily for supplemental links and context...")
            try:
                from tavily import TavilyClient
                tav_client = TavilyClient(api_key=tav_key)
                
                # Prerequisite blogs / context
                search_res = tav_client.search(f"{title} explanation tutorial background", max_results=3)
                context_data = "\n".join([r.get("content", "") for r in search_res.get("results", [])])
                
                # Related papers (papers citing or built on it)
                related_res = tav_client.search(f"papers citing or building on '{title}'", max_results=3)
                related_papers = []
                for r in related_res.get("results", []):
                    # MDPI Filter
                    if "mdpi.com" in r.get("url", "").lower() or "mdpi" in r.get("title", "").lower():
                        continue
                    related_papers.append(f"- [{r.get('title')}]({r.get('url')})")
                
                # Supplemental Youtube videos and GitHub repos
                yt_res = tav_client.search(f"{title} youtube video tutorial explanation", max_results=2)
                for r in yt_res.get("results", []):
                    u = r.get("url", "")
                    if ("youtube.com" in u or "youtu.be" in u) and u not in youtube_links:
                        youtube_links.append(u)
                        
                gh_res = tav_client.search(f"{title} github repository code implementation", max_results=2)
                for r in gh_res.get("results", []):
                    u = r.get("url", "")
                    if "github.com" in u and u not in github_links:
                        github_links.append(u)
                        
                # Supplemental HuggingFace spaces/models
                hf_res = tav_client.search(f"{title} huggingface space model", max_results=2)
                for r in hf_res.get("results", []):
                    u = r.get("url", "")
                    if "huggingface.co" in u and u not in hf_links:
                        hf_links.append(u)

                # Supplemental Twitter threads
                tw_res = tav_client.search(f"\"{title}\" site:twitter.com OR site:x.com", max_results=2)
                for r in tw_res.get("results", []):
                    u = r.get("url", "")
                    if u not in twitter_links:
                        twitter_links.append(u)

                # Supplemental Reddit threads
                rd_res = tav_client.search(f"\"{title}\" site:reddit.com", max_results=2)
                for r in rd_res.get("results", []):
                    u = r.get("url", "")
                    if u not in reddit_links:
                        reddit_links.append(u)
                        
            except Exception as e:
                print(f"⚠️ Tavily context/related/video search failed: {e}")
        else:
            print("⚠️ TAVILY_API_KEY not found. Fallback to free youtube search if needed.")
            if not youtube_links:
                youtube_links = free_youtube_search(f"{title} explanation tutorial")

        # Dedicated paper notebook
        clean_title = re.sub(r'[^\w\s-]', '', title).strip()[:50].strip()
        paper_nb_id = get_notebook_id(title=f"Paper-{clean_title}")

        # Ingest PDF
        pdf_path = download_arxiv_pdf(url)
        if not pdf_path and title:
            pdf_path = download_arxiv_pdf_by_title(title)
        if pdf_path and paper_nb_id:
            try:
                res_add = subprocess.run(["notebooklm", "source", "add", pdf_path, "--notebook", paper_nb_id, "--type", "file", "--json"], capture_output=True, text=True)
                src_id = json.loads(res_add.stdout).get("id") or json.loads(res_add.stdout).get("source", {}).get("id")
                if src_id:
                    subprocess.run(["notebooklm", "source", "wait", src_id, "--notebook", paper_nb_id, "--timeout", "300"], capture_output=True)
            except Exception as e:
                print(f"⚠️ Ingesting PDF into paper notebook failed: {e}")

        # Ingest Youtube, Github, and HuggingFace links into NotebookLM
        for yt in youtube_links:
            try:
                subprocess.run(["notebooklm", "source", "add", yt, "--notebook", paper_nb_id, "--type", "youtube", "--json"], capture_output=True)
            except Exception as e:
                print(f"⚠️ Ingesting YouTube video into notebook failed: {e}")
                
        for gh in github_links:
            try:
                subprocess.run(["notebooklm", "source", "add", gh, "--notebook", paper_nb_id, "--type", "url", "--json"], capture_output=True)
            except Exception as e:
                print(f"⚠️ Ingesting GitHub link into notebook failed: {e}")

        for hf in hf_links:
            try:
                subprocess.run(["notebooklm", "source", "add", hf, "--notebook", paper_nb_id, "--type", "url", "--json"], capture_output=True)
            except Exception as e:
                print(f"⚠️ Ingesting HuggingFace link into notebook failed: {e}")

        for tw in twitter_links:
            try:
                subprocess.run(["notebooklm", "source", "add", tw, "--notebook", paper_nb_id, "--type", "url", "--json"], capture_output=True)
            except Exception as e:
                print(f"⚠️ Ingesting Twitter link into notebook failed: {e}")

        for rd in reddit_links:
            try:
                subprocess.run(["notebooklm", "source", "add", rd, "--notebook", paper_nb_id, "--type", "url", "--json"], capture_output=True)
            except Exception as e:
                print(f"⚠️ Ingesting Reddit link into notebook failed: {e}")

        # Ingest related paper urls if they are valid webpages
        for rp in related_res.get("results", []):
            rp_url = rp.get("url", "")
            if rp_url and "mdpi" not in rp_url.lower():
                try:
                    subprocess.run(["notebooklm", "source", "add", rp_url, "--notebook", paper_nb_id, "--type", "url", "--json"], capture_output=True)
                except Exception as e:
                    print(f"⚠️ Ingesting related paper url into notebook failed: {e}")

        if context_data and paper_nb_id:
            try:
                subprocess.run(["notebooklm", "source", "add", context_data, "--notebook", paper_nb_id, "--type", "text", "--title", "Web Context", "--json"], capture_output=True)
            except Exception as e:
                print(f"⚠️ Ingesting web context into paper notebook failed: {e}")

        # Subject-specific category check
        text_to_match = (title + " " + description + " " + " ".join(prereqs) + " " + metric).lower()
        domain = "General AI"
        domain_header = "🧠 General Model & AI Details"
        domain_prompt = "What are the core model parameter counts, pretraining datasets, fine-tuning setups, or architectural innovations?"
        
        if any(w in text_to_match for w in ["robot", "pick", "place", "servo", "manipulation", "kinematics", "pickit"]):
            domain = "Robotics"
            domain_header = "🤖 Robotics Methodology"
            domain_prompt = "What arm models, grippers, sensor configurations, or coordinate mapping frames are used? What simulation (Isaac Sim, PyBullet) or real platforms validate it?"
        elif any(w in text_to_match for w in ["mri", "medical", "segmentation", "skull", "brain", "u-net"]):
            domain = "Medical Imaging"
            domain_header = "🏥 Medical Imaging Details"
            domain_prompt = "What modal sequences (T1, T2, FLAIR) and datasets (BraTS, OASIS) are used? What medical segmentation networks or loss functions are implemented?"
        elif any(w in text_to_match for w in ["agent", "assistant", "workflow", "tooling", "rag", "orchestration", "googooli"]):
            domain = "AI Agents & Assistants"
            domain_header = "🤖 AI Agent & Assistant Features"
            domain_prompt = "What multi-agent frameworks, tool usage, planning, memory, or RAG orchestration architectures are proposed?"

        # Single Unified Synthesis Query to NotebookLM
        report_text = ""
        mind_map_mermaid = ""

        if paper_nb_id:
            try:
                # 1. Ask for cohesive, non-repetitive literature report
                unified_prompt = f"""Generate a highly professional, cohesive literature study guide and analysis of this paper.
Do NOT use numerical citations like [1] or [2] in your output.
Structure the report using clean markdown headers:
1. Executive Summary: A concise overview of the paper and its significance.
2. Core Methodology & Mathematical Formulations: Detailed explanation of the algorithms, math formulas, and architectural innovations.
3. {domain_header}: {domain_prompt}
4. Novelty, Limitations & Failure Cases: Contrast with previous SOTA and list critical assumptions and failure conditions.
5. Reproduction & Training Setup: Key hyperparameters, datasets, hardware requirements, and training times.
6. Integration Ideas: Concrete ways to apply the paper's insights to Farhad's projects (e.g., object tracking, anomaly detection, medical brain MRI segmentation, robotics pick-and-place, or digital twins)."""

                if user_notes:
                    unified_prompt += f" Keep in mind these specific interests of Farhad: '{user_notes}'."

                report_text = run_notebooklm_ask(unified_prompt, paper_nb_id, resolve_references=True, use_personality=True)

                # 2. Generate native mind-map
                subprocess.run(["notebooklm", "generate", "mind-map", "--notebook", paper_nb_id], capture_output=True)
                mm_path = os.path.join(TEMP_DIR, f"mind_map_{paper_nb_id}.json")
                subprocess.run(["notebooklm", "download", "mind-map", mm_path, "--notebook", paper_nb_id, "--force"], capture_output=True)
                if os.path.exists(mm_path):
                    mind_map_mermaid = convert_json_mind_map_to_mermaid(mm_path)
                    os.remove(mm_path)

            except Exception as e:
                print(f"⚠️ NotebookLM Q&A or mind map generation failed: {e}")

        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

        # Build Obsidian note directory
        folder_path = os.path.join(VAULT_ROOT, "05-Learning", "Daily-Learn", clean_title)
        os.makedirs(folder_path, exist_ok=True)
        note_path = os.path.join(folder_path, "Overview.md")

        # Backlinks to vault projects
        backlinks = []
        for project in ["embedded-vision-tracker", "Battery-Cell-Anomaly-Detection---Foundation-Model", "pickit", "skull stripping", "learning-factory-project"]:
            if project.lower() in title.lower() or project.lower() in description.lower():
                backlinks.append(f"- [[02-Projects/{project}]]")

        backlinks_text = "\n".join(backlinks) if backlinks else "- None identified"

        # Multi-File Note Generation for Prerequisites (Recursive)
        prereqs_links = []
        for pr in prereqs:
            link_text = generate_prerequisite_note_recursive(pr, paper_nb_id, depth=0)
            if link_text:
                prereqs_links.append(link_text)

        prereqs_text = "\n".join(prereqs_links) if prereqs_links else "- None identified"

        # Format links list
        media_links = []
        for yt in youtube_links:
            media_links.append(f"- [YouTube Video]({yt})")
        for gh in github_links:
            media_links.append(f"- [GitHub Code]({gh})")
        for hf in hf_links:
            media_links.append(f"- [HuggingFace Space/Model]({hf})")
        for tw in twitter_links:
            media_links.append(f"- [Twitter Discussion]({tw})")
        for rd in reddit_links:
            media_links.append(f"- [Reddit Discussion]({rd})")
            
        today_str = get_netherlands_time().strftime("%Y-%m-%d")
        
        note_content = f"""# {title}

**Source:** {source} ({metric})
**Link:** [{url}]({url})
**Date Processed:** {today_str}

---

## 🔗 Project Connections
{backlinks_text}

---

## 📚 Prerequisite Concepts
{prereqs_text}

---

## 📎 Media & Resources
{"\n".join(media_links) if media_links else "- No external media linked"}

---

## 📝 Paper Summary
{description}

---

## 📄 Related Papers
{"\n".join(related_papers) if related_papers else "- No citations discovered"}

---

{report_text if report_text else "Literature study guide generation failed."}

---

## 🗺️ NotebookLM Mind Map
{mind_map_mermaid if mind_map_mermaid else "Mind map generation failed."}
"""

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(note_content)

        print(f"✅ Note created: {note_path}")

        # Auto-link to Daily Note and index to ensure proper ingestion/indexing into knowledge base
        try:
            link_note_to_daily_note(title, f"Daily-Learn/{clean_title}", today_str)
            update_research_index_note(title, f"Daily-Learn/{clean_title}", today_str)
        except Exception as ex:
            print(f"⚠️ Vault linking failed: {ex}")

        cursor.execute("UPDATE suggestions SET processed = 1 WHERE id = ?", (sug_id,))
        conn.commit()

        # HTML Telegram notification
        msg = f"🔬 <b>Research Note Created</b>\nSaved study guide report, parsed mind-map and prerequisites for: <i>{html.escape(title)}</i> under 05-Learning/Daily-Learn/{clean_title}."
        bot.send_message(CHAT_ID, msg, parse_mode="HTML")

    conn.close()
    print("✅ Phase 2 complete.")


def run_weekly_autotuning():
    """Phase 3: Weekly Interest Autotuning."""
    print("🌅 Running Weekly Interest Autotuning...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    seven_days_ago = time.time() - (7 * 24 * 3600)
    cursor.execute("""
    SELECT s.title, s.description, u.user_response 
    FROM user_selections u
    JOIN suggestions s ON u.suggestion_id = s.id
    WHERE CAST(u.timestamp AS REAL) > ?
    """, (seven_days_ago,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No user selection communications in the last week. Skipping autotuning.")
        return

    accepted_topics = []
    rejected_topics = []
    for title, desc, resp in rows:
        if resp == 'accepted':
            accepted_topics.append(title)
        else:
            rejected_topics.append(title)

    example_json = '{"add": ["graph neural networks"], "remove": ["digital twin"]}'
    prompt = (
        f"Based on Farhad's accepted research papers:\n{json.dumps(accepted_topics)}\n\n"
        f"And rejected research papers:\n{json.dumps(rejected_topics)}\n\n"
        f"Suggest 1 to 2 new keywords to ADD to his interests, and 1 to 2 keywords to REMOVE.\n"
        f"Format the output strictly as a JSON object with 'add' and 'remove' lists (e.g. {example_json})."
    )

    try:
        res = subprocess.run(["agy", "--print", prompt], capture_output=True, text=True, check=True)
        json_match = re.search(r"\{.*\}", res.stdout, re.DOTALL)
        if json_match:
            changes = json.loads(json_match.group(0))
        else:
            print("Failed to parse LLM suggestion.")
            return
    except Exception as e:
        print(f"⚠️ LLM autotuning proposal failed: {e}")
        changes = {"add": [], "remove": []}

    if not changes.get("add") and not changes.get("remove"):
        print("No keyword updates proposed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = time.strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO pending_changes (changes_json, created_date) VALUES (?, ?)",
                   (json.dumps(changes), today))
    conn.commit()
    changes_id = cursor.lastrowid
    conn.close()

    add_text = ", ".join([f"<code>{k}</code>" for k in changes.get("add", [])]) if changes.get("add") else "None"
    remove_text = ", ".join([f"<code>{k}</code>" for k in changes.get("remove", [])]) if changes.get("remove") else "None"

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton("✅ Approve Update", callback_data=f"interests_accept:{changes_id}")
    btn_no = types.InlineKeyboardButton("❌ Reject Update", callback_data=f"interests_reject:{changes_id}")
    markup.add(btn_yes, btn_no)

    interests_file_path = os.path.join(VAULT_ROOT, "07-Tools/Googooli-Research-Interests.md")
    msg_text = (
        f"<b>📊 Weekly Interests Autotuning Proposal</b>\n\n"
        f"Based on last week's selections, I propose updating your keywords:\n\n"
        f"➕ <b>Add Keywords:</b> {add_text}\n"
        f"➖ <b>Remove Keywords:</b> {remove_text}\n\n"
        f"Approve to update <a href='file://{interests_file_path}'>Googooli-Research-Interests.md</a>."
    )

    try:
        bot.send_message(CHAT_ID, msg_text, parse_mode="HTML", reply_markup=markup)
        print("✅ Weekly proposal sent to Telegram.")
    except Exception as te:
        print(f"⚠️ Failed to send weekly Telegram proposal: {te}")


def run_project_research(project_name):
    """Phase 4: Project-focused Deep Research."""
    print(f"🌅 Running Project-focused Deep Research for: {project_name}")
    proj_path = None
    for folder in os.listdir(os.path.join(VAULT_ROOT, "02-Projects")):
        if folder != "meetings" and os.path.isdir(os.path.join(VAULT_ROOT, "02-Projects", folder)):
            if project_name.lower() in folder.lower():
                proj_path = os.path.join(VAULT_ROOT, "02-Projects", folder)
                break

    if not proj_path:
        msg = f"❌ Project '{project_name}' not found under 02-Projects."
        bot.send_message(CHAT_ID, msg)
        print(msg)
        return

    bot.send_message(CHAT_ID, f"🔍 <b>Project Research Started</b>\nScanning READMEs and TODOs inside: <i>{html.escape(os.path.basename(proj_path))}</i>...", parse_mode="HTML")

    project_context = ""
    for root, dirs, files in os.walk(proj_path):
        for file in files:
            if file.endswith((".md", ".txt")):
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        text = f.read()
                        if "todo" in text.lower() or "challenge" in text.lower() or "readme" in file.lower():
                            project_context += f"\nFile {file}:\n{text[:1000]}"
                except:
                    continue

    prompt = (
        f"Analyze this project context and generate 2 search queries to find academic papers/repos that can help resolve the tasks/challenges:\n\n"
        f"{project_context[:3000]}\n\n"
        f"Return queries as a simple list of 2 strings separated by a newline."
    )

    keywords = [os.path.basename(proj_path)]
    try:
        res = subprocess.run(["agy", "--print", prompt], capture_output=True, text=True, check=True)
        keywords = [line.strip().replace('"', "") for line in res.stdout.split("\n") if line.strip()][:2]
    except Exception as e:
        print(f"⚠️ Query generation failed: {e}")

    all_raw_candidates = []
    for kw in keywords:
        print(f"🔍 Searching solutions for: {kw}")
        all_raw_candidates.extend(run_papercash_search(kw))
        all_raw_candidates.extend(run_last30days_search(kw))

    if not all_raw_candidates:
        bot.send_message(CHAT_ID, f"⚠️ No matches found on web for: {keywords}")
        return

    top_candidates = sorted(all_raw_candidates, key=lambda x: x.get("final_score", 0.0), reverse=True)[:3]
    paper_nb_id = get_notebook_id(title=f"ProjectResearch-{os.path.basename(proj_path)}")

    if project_context:
        try:
            subprocess.run(["notebooklm", "source", "add", project_context[:5000], "--notebook", paper_nb_id, "--type", "text", "--title", "Project Context", "--json"], capture_output=True)
        except Exception as e:
            print(f"⚠️ Context upload failed: {e}")

    for c in top_candidates:
        pdf_path = download_arxiv_pdf(c.get("url"))
        if not pdf_path and c.get("title"):
            pdf_path = download_arxiv_pdf_by_title(c.get("title"))
        if pdf_path and paper_nb_id:
            try:
                res_add = subprocess.run(["notebooklm", "source", "add", pdf_path, "--notebook", paper_nb_id, "--type", "file", "--json"], capture_output=True, text=True)
                src_id = json.loads(res_add.stdout).get("id") or json.loads(res_add.stdout).get("source", {}).get("id")
                if src_id:
                    subprocess.run(["notebooklm", "source", "wait", src_id, "--notebook", paper_nb_id, "--timeout", "300"], capture_output=True)
            except Exception as e:
                print(f"⚠️ Paper upload failed: {e}")
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    solutions = ""
    if paper_nb_id:
        try:
            solutions = run_notebooklm_ask("Based on the project files and downloaded papers, draft concrete solutions, architecture proposals, and code examples addressing the challenges/todos. Do NOT use numerical citations like [1] or [2].", paper_nb_id)
        except Exception as e:
            print(f"⚠️ Q&A failed: {e}")

    report_path = os.path.join(proj_path, "Research-Report.md")
    report_content = f"""# Research & Development Report: {os.path.basename(proj_path)}

**Date:** {time.strftime("%Y-%m-%d")}
**Search Queries:** {", ".join(keywords)}

---

## 🔎 References & Literature Found
"""
    for c in top_candidates:
        report_content += f"- [{c.get('title')}]({c.get('url')}) ({c.get('source')})\n"

    report_content += f"""
---

## 🛠️ Solutions, Architecture & Implementations
{solutions if solutions else "Q&A failed or timed out."}
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    clean_proj_name = html.escape(os.path.basename(proj_path))
    msg = (
        f"🔬 <b>Research Report Ready</b>\n"
        f"Saved research report to <i>{clean_proj_name}/Research-Report.md</i>.\n\n"
        f"You can query the report directly here on Telegram:\n"
        f"• 📝 Get brief summary: <code>/get_report_summary {os.path.basename(proj_path)}</code>\n"
        f"• 📖 Get full report context: <code>/get_report_full {os.path.basename(proj_path)}</code>"
    )
    bot.send_message(CHAT_ID, msg, parse_mode="HTML")


def main():
    if len(sys.argv) < 2:
        print("Usage: research_assistant.py [--phase1|--phase2|--weekly|--manual]")
        sys.exit(1)

    opt = sys.argv[1]
    if opt == "--phase1":
        phase1_search_loop()
    elif opt == "--phase2":
        phase2_ingestion_loop()
    elif opt == "--weekly":
        run_weekly_autotuning()
    elif opt == "--manual":
        if len(sys.argv) < 3:
            print("Specify project name: research_assistant.py --manual <project_name>")
            sys.exit(1)
        run_project_research(sys.argv[2])
    else:
        print(f"Option {opt} not recognized.")


if __name__ == "__main__":
    main()
