import os
import telebot
import subprocess
import sys
import uuid
import re
import html
import markdown2
from telebot import types

# Googooli Telegram Gateway
# V1.3.2: Aggressive Noise Reduction & Stateless Stability

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT_ROOT = os.path.dirname(BASE_DIR)
ENV_PATH = os.path.join(BASE_DIR, "config/.env")
SESSION_FILE = os.path.join(BASE_DIR, "config/session_id")
MODEL_FILE = os.path.join(BASE_DIR, "config/model_selection")
HISTORY_FILE = os.path.join(BASE_DIR, "config/raw_history")

# Suppress Node.js Deprecation Warnings natively
os.environ["NODE_OPTIONS"] = "--no-deprecation"

# Load from .env
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                try:
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value.replace('"', "").replace("'", "")
                except ValueError: continue

token_env = os.getenv("GOOGOOLI_TELEGRAM_TOKEN")
chat_id_env = os.getenv("GOOGOOLI_CHAT_ID")

if not token_env:
    print("❌ GOOGOOLI_TELEGRAM_TOKEN not set.")
    sys.exit(1)

try:
    ALLOWED_USER_ID = int(chat_id_env)
except:
    print("❌ Invalid GOOGOOLI_CHAT_ID.")
    sys.exit(1)

bot = telebot.TeleBot(token_env)

# Global memory to track accumulated stdout of the current session
RAW_HISTORY = ""

# Global memory to track file uploads awaiting save decisions
PENDING_UPLOADS = {}

AVAILABLE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-pro",
    "gemini-3.1-flash-lite",
    "gemini-omni",
    "gemini-2.0-flash",
    "gemini-1.5-pro"
]

def load_raw_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except: pass
    return ""

def save_raw_history(text):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(text)
    except: pass

def get_session_info():
    """Returns True if a new session is needed."""
    if not os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "w") as f: f.write("active")
        return True
    return False

def get_selected_model():
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, "r") as f: return f.read().strip()
    return None

def set_selected_model(model_name):
    with open(MODEL_FILE, "w") as f: f.write(model_name)

def clean_output(text):
    if not text: return ""
    # Strip Node.js and Extension Manager noise
    text = re.sub(r'\[ExtensionManager\].*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'\[ERROR\] \[ImportProcessor\].*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'Discarding invalid hook.*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'\(node:\d+\) \[DEP\d+\].*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'\(Use node --trace-deprecation.*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'Hook registry initialized.*?\n', '', text)
    text = re.sub(r'name: \'googooli-.*?\n', '', text)
    text = re.sub(r'type: \'command\',.*?\n', '', text)
    text = re.sub(r'command: \'.googooli/scripts/.*?\n', '', text)
    text = re.sub(r'\}\n', '', text)
    
    # Strip Tool Validation noise
    text = re.sub(r'tools\.\d+: Invalid tool name\n?', '', text)
    text = re.sub(r'Error executing tool .*?: Tool execution denied by policy\.\n?', '', text)
    text = re.sub(r'Error executing tool .*?: File path .*? is ignored by configured ignore patterns\.\n?', '', text)
    text = re.sub(r'Error executing tool .*?: Tool .*? not found\.\n?', '', text)
    
    # Strip API Retry/Stack Trace noise
    text = re.sub(r'Attempt \d+ failed with status \d+.*?\n', '', text)
    text = re.sub(r'Retrying with backoff.*?\n', '', text)
    text = re.sub(r'Error: Request failed with status code \d+.*?\n', '', text)
    text = re.sub(r'\s+at file:///usr/local/lib/node_modules/.*?\n', '', text)
    text = re.sub(r'\s+at process\.processTicksAndRejections.*?\n', '', text)
    text = re.sub(r'\s+at async .*?\n', '', text)
    text = re.sub(r'\{\s+status: \d+\s+\}\n', '', text)
    
    # Strip standard startup logs
    text = re.sub(r'Ripgrep is not available.*?\n', '', text)
    text = re.sub(r'Warning: True color.*?\n', '', text)
    text = re.sub(r'Loaded cached credentials\.\n', '', text)
    text = re.sub(r'Obsidian vault connected.*?\n', '', text)
    text = re.sub(r'RAG index .*?\n', '', text)
    text = re.sub(r'WARNING: The following project-level hooks.*?\n', '', text)
    text = re.sub(r'\s+- googooli-pre-sync\n?', '', text)
    text = re.sub(r'\s+- googooli-post-sync\n?', '', text)
    text = re.sub(r'These hooks will be executed.*?\n', '', text)
    text = re.sub(r'please review the project settings.*?\n', '', text)
    
    # Strip internal AI markers
    text = re.sub(r'\[Thought:.*?\]', '', text)
    text = re.sub(r'/caveman \w+', '', text)
    text = re.sub(r'YOLO mode is .*?\n', '', text)
    text = re.sub(r'\x1b\[\d+m.*?request an update to the settings at: https://goo.gle/manage-gemini-cli \x1b\[0m\n?', '', text)

    # Strip agy and Antigravity CLI noise
    text = re.sub(r'\[agy\].*?\n', '', text)
    text = re.sub(r'\[Antigravity\].*?\n', '', text)
    text = re.sub(r'Sandbox restriction:.*?\n', '', text)
    text = re.sub(r'Session ID:.*?\n', '', text)

    # Strip Antigravity startup greetings
    text = re.sub(r'Hello\.\s+Antigravity\s+here\.\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Hello\.\s+Antigravity\s+here\.\s+How\s+help\?\n?', '', text, flags=re.IGNORECASE)

    return text.strip()

def safe_html(text):
    """Converts Markdown to basic Telegram-safe HTML."""
    if not text: return ""
    text = html.escape(text)
    text = re.sub(r'\[\[(.*?)\]\]', r'<b>\1</b>', text)
    text = text.replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&')
    raw_html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables"])
    raw_html = re.sub(r'<h\d>(.*?)</h\d>', r'<b>\1</b>', raw_html)
    raw_html = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', raw_html)
    raw_html = re.sub(r'<em>(.*?)</em>', r'<i>\1</i>', raw_html)
    raw_html = re.sub(r'<li>', '• ', raw_html)
    raw_html = re.sub(r'</li>', '\n', raw_html)
    raw_html = re.sub(r'<div class="codehilite"><pre>', '<pre>', raw_html)
    raw_html = re.sub(r'</pre></div>', '</pre>', raw_html)
    allowed = ['b', 'i', 'u', 's', 'code', 'pre', 'a']
    def strip_unsupported(match):
        tag = match.group(1).lower().strip('/')
        tag_name = tag.split()[0]
        return match.group(0) if tag_name in allowed else ""
    final_html = re.sub(r'<(/?.*?)>', strip_unsupported, raw_html)
    return final_html.strip()

def run_agent(prompt, selected_model, is_retry=False):
    is_new = get_session_info()
    
    system_instruction = (
        "[System: Running in Telegram. If the user requests a file (e.g. a local note, PDF, image, music), "
        "do NOT print its contents. Instead, locate or save the file on disk and output exactly "
        "\"ACTION_SEND_FILE: <absolute_path>\" to send the file.]\n\n"
    )
    prompt_with_instr = system_instruction + prompt
    
    # Try running with agy (Antigravity) first
    cmd = [
        "agy",
        "--dangerously-skip-permissions",
        "--print", prompt_with_instr
    ]
    if selected_model:
        cmd.extend(["--model", selected_model])
    if not is_new:
        cmd.append("--continue")
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result, False
        else:
            print(f"⚠️ agy failed with code {result.returncode}. Falling back to gemini...")
    except Exception as e:
        print(f"⚠️ Exception running agy: {str(e)}. Falling back to gemini...")
        
    # LEGACY FALLBACK: Run with gemini
    allowed_tools = [
        "run_shell_command", "google_web_search", "web_fetch",
        "read_file", "write_file", "replace", "list_directory", "glob",
        "mcp_gemini-obsidian_obsidian_rag_query",
        "mcp_gemini-obsidian_obsidian_read_note",
        "mcp_gemini-obsidian_obsidian_get_daily_note",
        "mcp_gemini-obsidian_obsidian_insert_at_heading",
        "mcp_gemini-obsidian_obsidian_append_note",
        "mcp_gemini-obsidian_obsidian_replace_in_note"
    ]
    legacy_cmd = [
        "gemini", "--approval-mode", "auto_edit", 
        "--allowed-tools", ",".join(allowed_tools),
        "-p", prompt_with_instr
    ]
    if selected_model:
        legacy_cmd.extend(["-m", selected_model])
    if not is_new:
        legacy_cmd.extend(["--resume", "latest"])
        
    legacy_result = subprocess.run(legacy_cmd, capture_output=True, text=True)
    combined_output = legacy_result.stdout + legacy_result.stderr
    
    if "Invalid session identifier" in combined_output or "No previous sessions found" in combined_output:
        if not is_retry:
            print("⚠️ Session invalid. Auto-recovering...")
            if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
            return run_agent(prompt, selected_model, is_retry=True)
            
    return legacy_result, True

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📊 Project Status")
    btn2 = types.KeyboardButton("📑 Tonight's Papers")
    btn3 = types.KeyboardButton("🎯 Select Model")
    btn4 = types.KeyboardButton("🔬 Diagnostics")
    btn5 = types.KeyboardButton("🧹 Reset Session")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4, btn5)
    return markup

def show_project_status(message):
    try:
        vault_root = os.path.dirname(BASE_DIR)
        todo_path = os.path.join(vault_root, "TODO.md")
        active_projects_text = ""
        
        if os.path.exists(todo_path):
            with open(todo_path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r"## 🚀 Active Projects(.*?)(?:##|\Z)", content, re.DOTALL)
            if match:
                active_projects_text = match.group(1).strip()
        
        proj_dir = os.path.join(vault_root, "02-Projects")
        all_projects = []
        if os.path.exists(proj_dir):
            all_projects = [d for d in os.listdir(proj_dir) if os.path.isdir(os.path.join(proj_dir, d)) and not d.startswith(".")]
            
        proj_list = "\n".join([f"• {p}" for p in all_projects if p != "meetings"])
        
        response_text = "<b>📊 Active Projects Status</b>\n\n"
        if active_projects_text:
            cleaned_todo = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', r'<b>\1</b>', active_projects_text)
            response_text += f"<b>Current TODO Tasks:</b>\n{cleaned_todo}\n\n"
        
        response_text += f"<b>All Registered Projects:</b>\n{proj_list}"
        
        bot.send_message(message.chat.id, response_text, parse_mode='HTML', reply_markup=get_main_keyboard())
    except Exception as e:
        bot.reply_to(message, f"❌ Error retrieving project status: {str(e)}")

def show_tonight_papers(message):
    try:
        vault_root = os.path.dirname(BASE_DIR)
        todo_path = os.path.join(vault_root, "TODO.md")
        learning_queue_text = ""
        
        if os.path.exists(todo_path):
            with open(todo_path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r"## 📚 Learning Queue.*?\n(.*?)(\n##|\n---|\Z)", content, re.DOTALL)
            if match:
                learning_queue_text = match.group(1).strip()
                
        db_path = os.path.join(BASE_DIR, "data/research_state.db")
        db_papers = []
        if os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("SELECT title, url FROM suggestions WHERE status = 'accepted' AND processed = 0")
                db_papers = c.fetchall()
                conn.close()
            except Exception as dbe:
                print(f"Database query failed: {dbe}")
                
        response_text = "<b>📑 Tonight's Study & Investigation</b>\n\n"
        
        if db_papers:
            response_text += "<b>Accepted Papers for Deep Processing:</b>\n"
            for title, url in db_papers:
                response_text += f"• <a href=\"{url}\">{html.escape(title)}</a>\n"
            response_text += "\n"
            
        if learning_queue_text:
            cleaned_queue = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', r'<b>\1</b>', learning_queue_text)
            response_text += f"<b>Learning Queue (from TODO):</b>\n{cleaned_queue}\n"
        else:
            response_text += "<i>No papers in the queue today. Upload a paper or use /research to add more!</i>"
            
        bot.send_message(message.chat.id, response_text, parse_mode='HTML', reply_markup=get_main_keyboard())
    except Exception as e:
        bot.reply_to(message, f"❌ Error retrieving papers queue: {str(e)}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.from_user.id != ALLOWED_USER_ID: return
    welcome_text = (
        "🤖 <b>Welcome to Googooli Assistant!</b>\n\n"
        "I am ready to help you manage your Obsidian vault, research papers, and software projects.\n\n"
        "Use the quick menu buttons below for common functions, or type a request directly."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=get_main_keyboard())

@bot.message_handler(commands=['clear', 'reset'])
def handle_clear(message):
    if message.from_user.id != ALLOWED_USER_ID: return
    global RAW_HISTORY
    RAW_HISTORY = ""
    if os.path.exists(HISTORY_FILE):
        try: os.remove(HISTORY_FILE)
        except: pass
    if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
    bot.reply_to(message, "🧹 Session reset. Starting fresh.", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['model'])
def handle_model(message):
    if message.from_user.id != ALLOWED_USER_ID: return
    markup = types.InlineKeyboardMarkup(row_width=1)
    curr = get_selected_model()
    btns = [types.InlineKeyboardButton(f"✅ {m}" if m == curr else m, callback_data=f"set_model:{m}") for m in AVAILABLE_MODELS]
    btns.append(types.InlineKeyboardButton("✅ Default" if curr is None else "Default", callback_data="set_model:default"))
    markup.add(*btns)
    bot.send_message(message.chat.id, "🎯 Select model:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_model:"))
def callback_set_model(call):
    if call.from_user.id != ALLOWED_USER_ID: return
    model_name = call.data.split(":")[1]
    if model_name == "default":
        if os.path.exists(MODEL_FILE): os.remove(MODEL_FILE)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🎯 Model: `Default`")
    else:
        set_selected_model(model_name)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"🎯 Model: `{model_name}`")

def process_file_prompt(chat_id, prompt, reply_to_message_id, file_path=None):
    global RAW_HISTORY
    if not RAW_HISTORY:
        RAW_HISTORY = load_raw_history()
    bot.send_message(chat_id, f"⚙️ Processing file with prompt: \"{prompt}\"...")
    
    pre_script = os.path.join(BASE_DIR, "scripts/pre_sync.sh")
    post_script = os.path.join(BASE_DIR, "scripts/post_sync.sh")
    subprocess.run(["/bin/bash", pre_script], capture_output=True)
    
    try:
        selected_model = get_selected_model()
        result, fallback = run_agent(prompt, selected_model)
        stdout = result.stdout if result.stdout else ""
        if RAW_HISTORY and stdout.startswith(RAW_HISTORY):
            new_raw = stdout[len(RAW_HISTORY):]
        else:
            new_raw = stdout
        RAW_HISTORY = stdout
        save_raw_history(RAW_HISTORY)
        raw_output = clean_output(new_raw)
        if fallback:
            raw_output = "⚠️ <b>Warning</b>: <i>Googooli executing in legacy Gemini CLI fallback mode.</i>\n\n" + raw_output
        
        file_matches = re.findall(r'ACTION_SEND_FILE:\s*(.*)', raw_output)
        vault_root = os.path.dirname(BASE_DIR)
        for out_file_path in file_matches:
            out_file_path = out_file_path.strip()
            if os.path.exists(out_file_path):
                try:
                    with open(out_file_path, 'rb') as f:
                        bot.send_document(chat_id, f, reply_to_message_id=reply_to_message_id)
                    if "00-Inbox/temp/" in out_file_path:
                        bin_dir = os.path.join(vault_root, "00-Inbox/.bin")
                        os.makedirs(bin_dir, exist_ok=True)
                        os.rename(out_file_path, os.path.join(bin_dir, os.path.basename(out_file_path)))
                except Exception as fe:
                    bot.send_message(chat_id, f"❌ Send error: {str(fe)}")
            else:
                bot.send_message(chat_id, f"⚠️ Not found: `{out_file_path}`")
        
        raw_output = re.sub(r'ACTION_SEND_FILE:.*', '', raw_output).strip()
        
        if not raw_output and not file_matches:
            bot.send_message(chat_id, "✅ Task completed.", reply_to_message_id=reply_to_message_id, reply_markup=get_main_keyboard())
        elif raw_output:
            formatted = safe_html(raw_output)
            if len(formatted) > 4000:
                for i in range(0, len(formatted), 4000):
                    bot.send_message(chat_id, formatted[i:i+4000], parse_mode='HTML', reply_to_message_id=reply_to_message_id, reply_markup=get_main_keyboard())
            else:
                bot.send_message(chat_id, formatted, parse_mode='HTML', reply_to_message_id=reply_to_message_id, reply_markup=get_main_keyboard())
        
        subprocess.run(["/bin/bash", post_script], capture_output=True)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error processing: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_save:"))
def callback_upload_save(call):
    if call.from_user.id != ALLOWED_USER_ID: return
    parts = call.data.split(":")
    action = parts[1]
    file_session_id = parts[2]
    
    if file_session_id not in PENDING_UPLOADS:
        bot.answer_callback_query(call.id, "Session expired or invalid.")
        return
        
    info = PENDING_UPLOADS[file_session_id]
    
    if action == "no":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📥 Received file: `{info['name']}`\nStatus: ❌ Not saved to vault."
        )
        if info['caption']:
            process_file_prompt(call.message.chat.id, info['caption'], info['message_id'], None)
        PENDING_UPLOADS.pop(file_session_id, None)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_temp = types.InlineKeyboardButton("Inbox Temp (00-Inbox/temp/)", callback_data=f"upload_dir:temp:{file_session_id}")
        btn_custom = types.InlineKeyboardButton("Custom directory...", callback_data=f"upload_dir:custom:{file_session_id}")
        markup.add(btn_temp, btn_custom)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📥 Received file: `{info['name']}`\nSelect save directory:",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_dir:"))
def callback_upload_dir(call):
    if call.from_user.id != ALLOWED_USER_ID: return
    parts = call.data.split(":")
    dir_choice = parts[1]
    file_session_id = parts[2]
    
    if file_session_id not in PENDING_UPLOADS:
        bot.answer_callback_query(call.id, "Session expired or invalid.")
        return
        
    info = PENDING_UPLOADS[file_session_id]
    
    if dir_choice == "temp":
        vault_root = os.path.dirname(BASE_DIR)
        dest_dir = os.path.join(vault_root, "00-Inbox/temp")
        os.makedirs(dest_dir, exist_ok=True)
        file_path = os.path.join(dest_dir, info['name'])
        
        try:
            with open(file_path, 'wb') as f:
                f.write(info['data'])
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"📥 Received file: `{info['name']}`\nStatus: ✅ Saved to `00-Inbox/temp/`."
            )
            
            if info['caption']:
                process_file_prompt(call.message.chat.id, info['caption'], info['message_id'], file_path)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error saving file: {str(e)}")
            
        PENDING_UPLOADS.pop(file_session_id, None)
        
    elif dir_choice == "custom":
        sent_msg = bot.send_message(
            call.message.chat.id,
            f"Please reply to this message with the directory path (relative to Vault root, e.g. `02-Projects/MyProject`):",
            reply_markup=types.ForceReply(selective=True)
        )
        bot.register_next_step_handler(sent_msg, handle_custom_save_path, file_session_id, call.message.message_id)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📥 Received file: `{info['name']}`\nStatus: Waiting for custom directory path..."
        )

def handle_custom_save_path(message, file_session_id, original_prompt_msg_id):
    if message.from_user.id != ALLOWED_USER_ID: return
    if file_session_id not in PENDING_UPLOADS:
        bot.reply_to(message, "❌ Session expired or invalid.")
        return
        
    info = PENDING_UPLOADS[file_session_id]
    
    if not message.text:
        bot.reply_to(message, "❌ Invalid text input. Please reply with a text path or type /cancel to abort.")
        sent_msg = bot.send_message(
            message.chat.id,
            "Please enter a valid relative path (e.g. `02-Projects/ProjectA`):",
            reply_markup=types.ForceReply(selective=True)
        )
        bot.register_next_step_handler(sent_msg, handle_custom_save_path, file_session_id, original_prompt_msg_id)
        return

    rel_path = message.text.strip()
    
    if rel_path.startswith("/"):
        bot.reply_to(message, "❌ File upload custom path cancelled.")
        PENDING_UPLOADS.pop(file_session_id, None)
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_prompt_msg_id,
                text=f"📥 Received file: `{info['name']}`\nStatus: ❌ Cancelled custom path selection."
            )
        except Exception:
            pass
        return
        
    if ".." in rel_path:
        bot.reply_to(message, "❌ Invalid path. Cannot contain '..'. Please try again.")
        sent_msg = bot.send_message(
            message.chat.id,
            "Please enter a valid relative path (e.g. `02-Projects/ProjectA`):",
            reply_markup=types.ForceReply(selective=True)
        )
        bot.register_next_step_handler(sent_msg, handle_custom_save_path, file_session_id, original_prompt_msg_id)
        return
        
    vault_root = os.path.dirname(BASE_DIR)
    dest_dir = os.path.abspath(os.path.join(vault_root, rel_path))
    
    if not dest_dir.startswith(os.path.abspath(vault_root)):
        bot.reply_to(message, "❌ Path is outside the vault. Please try again.")
        sent_msg = bot.send_message(
            message.chat.id,
            "Please enter a valid relative path (e.g. `02-Projects/ProjectA`):",
            reply_markup=types.ForceReply(selective=True)
        )
        bot.register_next_step_handler(sent_msg, handle_custom_save_path, file_session_id, original_prompt_msg_id)
        return
        
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, info['name'])
    
    try:
        with open(file_path, 'wb') as f:
            f.write(info['data'])
            
        bot.reply_to(message, f"✅ Saved file `{info['name']}` to `{rel_path}/`.")
        
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_prompt_msg_id,
                text=f"📥 Received file: `{info['name']}`\nStatus: ✅ Saved to `{rel_path}/`."
            )
        except Exception:
            pass
            
        if info['caption']:
            process_file_prompt(message.chat.id, info['caption'], info['message_id'], file_path)
    except Exception as e:
        bot.reply_to(message, f"❌ Error saving file: {str(e)}")
        
    PENDING_UPLOADS.pop(file_session_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("research_"))
def callback_research_selection(call):
    if call.from_user.id != ALLOWED_USER_ID: return
    action, suggestion_id = call.data.split(":")
    
    import sqlite3
    import time
    db_path = os.path.join(BASE_DIR, "data/research_state.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if action == "research_accept":
            new_status = 'accepted'
            status_label = "✅ Accepted"
        elif action == "research_reject":
            new_status = 'rejected'
            status_label = "❌ Rejected"
        else: # research_later
            new_status = 'later'
            status_label = "⏳ Left for Later"
            
        cursor.execute("UPDATE suggestions SET status = ? WHERE id = ?", (new_status, suggestion_id))
        cursor.execute("INSERT INTO user_selections (suggestion_id, user_response, timestamp) VALUES (?, ?, ?)",
                       (suggestion_id, new_status, str(time.time())))
        conn.commit()
        conn.close()
        
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        bot.send_message(call.message.chat.id, f"{status_label} item #{suggestion_id}!", reply_to_message_id=call.message.message_id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("guided_"))
def callback_guided_research(call):
    if call.from_user.id != ALLOWED_USER_ID: return
    action, project_name = call.data.split(":", 1)
    
    import sqlite3
    import threading
    db_path = os.path.join(BASE_DIR, "data/research_state.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if action == "guided_proceed":
            cursor.execute("UPDATE guided_research SET status = 'running' WHERE project_name = ?", (project_name,))
            conn.commit()
            conn.close()
            
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, f"🚀 Resuming research for: <b>{project_name}</b>...", parse_mode="HTML")
            
            # Import dynamically to avoid circular import issues
            from research_assistant import run_project_research
            threading.Thread(target=run_project_research, args=(project_name,)).start()
            
        elif action == "guided_pause":
            cursor.execute("UPDATE guided_research SET status = 'idle' WHERE project_name = ?", (project_name,))
            conn.commit()
            conn.close()
            
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, f"⏸️ Research paused for: <b>{project_name}</b>. Edit <code>research_brief.md</code> and reply/proceed to resume.", parse_mode="HTML")
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("interests_"))
def callback_interests_selection(call):
    if call.from_user.id != ALLOWED_USER_ID: return
    action, changes_id = call.data.split(":")
    
    import sqlite3
    import json
    db_path = os.path.join(BASE_DIR, "data/research_state.db")
    interests_file = os.path.join(VAULT_ROOT, "07-Tools/Googooli-Research-Interests.md")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT changes_json FROM pending_changes WHERE id = ?", (changes_id,))
        row = cursor.fetchone()
        if not row:
            bot.answer_callback_query(call.id, "Error: changes not found")
            conn.close()
            return
            
        changes = json.loads(row[0])
        new_status = 'accepted' if action == "interests_accept" else 'rejected'
        cursor.execute("UPDATE pending_changes SET status = ? WHERE id = ?", (new_status, changes_id))
        conn.commit()
        conn.close()
        
        if new_status == 'accepted':
            with open(interests_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            kw_section_match = re.search(r"(## 4\. Current Target Keywords\s*\n\*Last Updated:[^\n]*\n)(.*)", content, re.DOTALL)
            if kw_section_match:
                prefix = kw_section_match.group(1)
                body = kw_section_match.group(2)
                
                keywords = re.findall(r"-\s*`([^`]+)`", body)
                for add_kw in changes.get("add", []):
                    if add_kw not in keywords:
                        keywords.append(add_kw)
                for rem_kw in changes.get("remove", []):
                    if rem_kw in keywords:
                        keywords.remove(rem_kw)
                        
                new_keywords_list = "\n".join([f"- `{kw}`" for kw in keywords])
                new_section = f"{prefix}{new_keywords_list}\n"
                new_content = content.replace(kw_section_match.group(0), new_section)
                
                with open(interests_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
            status_label = "✅ Keywords Updated"
        else:
            status_label = "❌ Keywords Rejected"
            
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        bot.send_message(call.message.chat.id, f"{status_label} successfully!", reply_to_message_id=call.message.message_id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)}")

@bot.message_handler(commands=['diagnose_research'])
def handle_diagnose_research(message):
    if message.from_user.id != ALLOWED_USER_ID: return
    bot.send_chat_action(message.chat.id, 'typing')
    script_path = os.path.join(BASE_DIR, "scripts/check_dependencies.sh")
    try:
        result = subprocess.run([script_path], capture_output=True, text=True)
        bot.reply_to(message, f"<pre>{html.escape(result.stdout)}</pre>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Diagnostics failed: {str(e)}")

@bot.message_handler(commands=['research'])
def handle_research_command(message):
    if message.from_user.id != ALLOWED_USER_ID: return
    args = message.text.split(None, 1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /research <project_name>")
        return
    proj_name = args[1].strip()
    bot.send_chat_action(message.chat.id, 'typing')
    script_path = os.path.join(BASE_DIR, "scripts/research_assistant.py")
    try:
        subprocess.Popen([sys.executable, script_path, "--manual", proj_name])
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to start research subprocess: {str(e)}")

def extract_report_summary(content):
    """Extracts a concise summary from the report content."""
    lines = content.split("\n")
    summary_lines = []
    in_references = False
    ref_count = 0
    
    for line in lines:
        if line.startswith("# "):
            summary_lines.append(f"<b>{line[2:].strip()}</b>\n")
        elif "Search Queries:" in line:
            summary_lines.append(line.strip())
        elif "References & Literature" in line:
            in_references = True
            summary_lines.append("\n<b>🔎 Key References Found:</b>")
        elif in_references:
            if line.startswith("---") or line.startswith("## "):
                in_references = False
            elif line.strip().startswith("-"):
                if ref_count < 3:
                    summary_lines.append(line.strip())
                    ref_count += 1
                elif ref_count == 3:
                    summary_lines.append("- ... and others (see full report)")
                    ref_count += 1
                    
    # Extract brief snippet of solutions
    solutions_match = re.search(r"## 🛠️ Solutions, Architecture & Implementations\s*(.*)", content, re.DOTALL)
    if solutions_match:
        sol_text = solutions_match.group(1).strip()
        sol_paragraphs = [p.strip() for p in sol_text.split("\n\n") if p.strip()]
        if sol_paragraphs:
            summary_lines.append("\n<b>🛠️ Core Solutions Preview:</b>")
            preview = sol_paragraphs[0]
            if len(preview) > 600:
                preview = preview[:600] + "..."
            summary_lines.append(preview)
            
    summary_lines.append("\n<i>Use /get_report_full <project> to read the full report.</i>")
    return "\n".join(summary_lines)


@bot.message_handler(commands=['get_report_summary'])
def handle_get_report_summary(message):
    if message.from_user.id != ALLOWED_USER_ID: return
    args = message.text.split(None, 1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /get_report_summary <project_name>")
        return
    proj_name = args[1].strip().lower()
    
    proj_dir = os.path.join(VAULT_ROOT, "02-Projects")
    report_path = None
    
    for folder in os.listdir(proj_dir):
        if proj_name in folder.lower():
            target_report = os.path.join(proj_dir, folder, "Research-Report.md")
            if os.path.exists(target_report):
                report_path = target_report
                break
                
    if not report_path:
        bot.reply_to(message, f"❌ Research report not found for project: {proj_name}")
        return
        
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        summary_md = extract_report_summary(content)
        formatted = safe_html(summary_md)
        bot.send_message(message.chat.id, formatted, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Read error: {str(e)}")


@bot.message_handler(commands=['get_report_full'])
def handle_get_report_full(message):
    if message.from_user.id != ALLOWED_USER_ID: return
    args = message.text.split(None, 1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /get_report_full <project_name>")
        return
    proj_name = args[1].strip().lower()
    
    proj_dir = os.path.join(VAULT_ROOT, "02-Projects")
    report_path = None
    
    for folder in os.listdir(proj_dir):
        if proj_name in folder.lower():
            target_report = os.path.join(proj_dir, folder, "Research-Report.md")
            if os.path.exists(target_report):
                report_path = target_report
                break
                
    if not report_path:
        bot.reply_to(message, f"❌ Research report not found for project: {proj_name}")
        return
        
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        formatted = safe_html(content)
        if len(formatted) > 4000:
            for i in range(0, len(formatted), 4000):
                bot.send_message(message.chat.id, formatted[i:i+4000], parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, formatted, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Read error: {str(e)}")

@bot.message_handler(content_types=['document', 'photo', 'audio', 'video', 'voice'])
def handle_file(message):
    if message.from_user.id != ALLOWED_USER_ID: return
    
    file_name = None
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_name = f"photo_{uuid.uuid4().hex[:6]}.jpg"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or f"audio_{uuid.uuid4().hex[:6]}.mp3"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or f"video_{uuid.uuid4().hex[:6]}.mp4"
    elif message.voice:
        file_id = message.voice.file_id
        file_name = f"voice_{uuid.uuid4().hex[:6]}.ogg"
    else:
        return
        
    bot.send_chat_action(message.chat.id, 'upload_document')
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_session_id = f"file_sess_{uuid.uuid4().hex[:8]}"
        PENDING_UPLOADS[file_session_id] = {
            'data': downloaded_file,
            'name': file_name,
            'caption': message.caption,
            'chat_id': message.chat.id,
            'message_id': message.message_id
        }
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_yes = types.InlineKeyboardButton("Save to Vault", callback_data=f"upload_save:yes:{file_session_id}")
        btn_no = types.InlineKeyboardButton("Do Not Save", callback_data=f"upload_save:no:{file_session_id}")
        markup.add(btn_yes, btn_no)
        
        bot.reply_to(message, f"📥 Received file: `{file_name}`\nDo you want to save it to the vault?", reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error handling file: {str(e)}")

@bot.message_handler(func=lambda message: message.reply_to_message is not None and message.from_user.id == ALLOWED_USER_ID)
def handle_reply_notes(message):
    replied_msg = message.reply_to_message
    text = replied_msg.text or replied_msg.caption or ""
    # Check for paper suggestion ID
    sug_id_match = re.search(r'ID:\s*(\d+)', text)
    if not sug_id_match:
        sug_id_match = re.search(r'<!-- ID:\s*(\d+) -->', text)
        
    # Check for guided project name
    project_match = re.search(r'guided project:\s*([^\n\r]+)', text, re.IGNORECASE)
    if not project_match:
        project_match = re.search(r'research for:\s*([^\n\r]+)', text, re.IGNORECASE)
        
    db_path = os.path.join(BASE_DIR, "data/research_state.db")
    
    if sug_id_match:
        sug_id = int(sug_id_match.group(1))
        user_note = message.text.strip()
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE suggestions SET user_notes = ? WHERE id = ?", (user_note, sug_id))
            conn.commit()
            conn.close()
            bot.reply_to(message, f"📝 <b>Note saved for paper #{sug_id}:</b>\n\"{html.escape(user_note)}\"\n\nThis will guide Phase 2 deep ingestion.", parse_mode='HTML')
            return
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to save note: {str(e)}")
            return
            
    elif project_match:
        project_name = project_match.group(1).strip()
        user_comment = message.text.strip()
        try:
            import sqlite3
            import threading
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE guided_research SET status = 'running' WHERE project_name = ?", (project_name,))
            conn.commit()
            conn.close()
            
            # Import dynamically to avoid circular dependencies
            from research_assistant import run_project_research
            threading.Thread(target=run_project_research, args=(project_name, user_comment)).start()
            
            bot.reply_to(message, f"📝 <b>Feedback received for project {project_name}:</b>\n\"{html.escape(user_comment)}\"\n\nResuming research phase...", parse_mode='HTML')
            return
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to resume project research: {str(e)}")
            return


@bot.message_handler(func=lambda message: message.from_user.id == ALLOWED_USER_ID)
def handle_command(message):
    prompt = message.text
    if not prompt: return
    
    if prompt == "📊 Project Status":
        show_project_status(message)
        return
    elif prompt == "📑 Tonight's Papers":
        show_tonight_papers(message)
        return
    elif prompt == "🎯 Select Model":
        handle_model(message)
        return
    elif prompt == "🔬 Diagnostics":
        handle_diagnose_research(message)
        return
    elif prompt == "🧹 Reset Session":
        handle_clear(message)
        return
        
    selected_model = get_selected_model()
    bot.send_chat_action(message.chat.id, 'typing')
    
    pre_script = os.path.join(BASE_DIR, "scripts/pre_sync.sh")
    post_script = os.path.join(BASE_DIR, "scripts/post_sync.sh")
    subprocess.run(["/bin/bash", pre_script], capture_output=True)
    
    try:
        global RAW_HISTORY
        if not RAW_HISTORY:
            RAW_HISTORY = load_raw_history()
        result, fallback = run_agent(prompt, selected_model)
        stdout = result.stdout if result.stdout else ""
        if RAW_HISTORY and stdout.startswith(RAW_HISTORY):
            new_raw = stdout[len(RAW_HISTORY):]
        else:
            new_raw = stdout
        RAW_HISTORY = stdout
        save_raw_history(RAW_HISTORY)
        raw_output = clean_output(new_raw)
        if fallback:
            raw_output = "⚠️ <b>Warning</b>: <i>Googooli executing in legacy Gemini CLI fallback mode.</i>\n\n" + raw_output
        
        file_matches = re.findall(r'ACTION_SEND_FILE:\s*(.*)', raw_output)
        for file_path in file_matches:
            file_path = file_path.strip()
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        bot.send_document(message.chat.id, f, reply_to_message_id=message.message_id)
                    if "00-Inbox/temp/" in file_path:
                        vault_root = os.path.dirname(BASE_DIR)
                        bin_dir = os.path.join(vault_root, "00-Inbox/.bin")
                        os.makedirs(bin_dir, exist_ok=True)
                        os.rename(file_path, os.path.join(bin_dir, os.path.basename(file_path)))
                except Exception as fe:
                    bot.send_message(message.chat.id, f"❌ Send error: {str(fe)}")
            else:
                bot.send_message(message.chat.id, f"⚠️ Not found: `{file_path}`")
        
        raw_output = re.sub(r'ACTION_SEND_FILE:.*', '', raw_output).strip()
        
        if not raw_output and not file_matches:
            bot.reply_to(message, "✅ Task completed.", reply_markup=get_main_keyboard())
        elif raw_output:
            formatted = safe_html(raw_output)
            if len(formatted) > 4000:
                for i in range(0, len(formatted), 4000):
                    bot.send_message(message.chat.id, formatted[i:i+4000], parse_mode='HTML', reply_to_message_id=message.message_id, reply_markup=get_main_keyboard())
            else:
                bot.send_message(message.chat.id, formatted, parse_mode='HTML', reply_to_message_id=message.message_id, reply_markup=get_main_keyboard())
        
        subprocess.run(["/bin/bash", post_script], capture_output=True)
        
    except telebot.apihelper.ApiTelegramException as te:
        plain = raw_output.replace("<", "").replace(">", "")
        bot.send_message(message.chat.id, plain[:4000], reply_to_message_id=message.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    is_dev_env = os.getenv("GOOGOOLI_DEV") == "true" or "--dev" in sys.argv
    
    if hostname == "mamdaliof" and not is_dev_env:
        print("⚠️ Googooli: Telegram gateway is disabled on personal PC (mamdaliof). Run with --dev or set GOOGOOLI_DEV=true to override.")
        sys.exit(0)

    print(f"🤖 Googooli Active ({ALLOWED_USER_ID})")
    bot.polling(none_stop=True)
