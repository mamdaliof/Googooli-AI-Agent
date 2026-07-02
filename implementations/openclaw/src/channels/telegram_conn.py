import os
import re
import html
import telebot
from telebot import types
from src.agent import OpenClawAgent

def to_telegram_html(text: str) -> str:
    # 1. Escape HTML special characters
    text = html.escape(text)
    # 2. Restore bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # 3. Restore italic
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # 4. Restore inline code
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    # 5. Restore preformatted code blocks
    text = re.sub(r'```(.*?)\n(.*?)```', r'<pre>\2</pre>', text, flags=re.DOTALL)
    # 6. Bullet points
    text = re.sub(r'^\s*-\s+(.*)', r'• \1', text, flags=re.MULTILINE)
    return text

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📊 Project Status")
    btn2 = types.KeyboardButton("🧹 Reset Session")
    markup.add(btn1, btn2)
    return markup

class TelegramConnector:
    def __init__(self, token: str, agent: OpenClawAgent):
        self.bot = telebot.TeleBot(token)
        self.agent = agent

        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            try:
                print(f"Received: '{message.text}'")
                reply = self.agent.handle_message(message.text, user_id=str(message.chat.id))
                print(f"Agent reply: '{reply}'")
                
                # Check for files to send
                file_matches = re.findall(r'ACTION_SEND_FILE:\s*(.*)', reply)
                for out_file_path in file_matches:
                    out_file_path = out_file_path.strip()
                    if os.path.exists(out_file_path):
                        try:
                            with open(out_file_path, 'rb') as f:
                                self.bot.send_document(message.chat.id, f, reply_to_message_id=message.message_id)
                        except Exception as fe:
                            self.bot.reply_to(message, f"❌ Send error: {str(fe)}")
                    else:
                        self.bot.reply_to(message, f"⚠️ Not found: `{out_file_path}`")
                
                # Remove action command line from final text reply
                clean_reply = re.sub(r'ACTION_SEND_FILE:.*', '', reply).strip()
                if clean_reply:
                    html_reply = to_telegram_html(clean_reply)
                    self.bot.send_message(
                        message.chat.id, 
                        html_reply, 
                        parse_mode='HTML', 
                        reply_to_message_id=message.message_id,
                        reply_markup=get_main_keyboard()
                    )
            except Exception as e:
                self.bot.reply_to(message, f"Error processing request: {e}")

    def run(self):
        print("Starting Telegram Bot Connector...")
        self.bot.infinity_polling()
