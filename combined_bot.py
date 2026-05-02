import asyncio
import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from pyrogram import Client, filters
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")

# --- AI Setup ---
genai.configure(api_key=GEMINI_API_KEY)
SYSTEM_PROMPT = """
Siz foydalanuvchining shaxsiy va aqlli yordamchisisiz. Vazifangiz - lichkasiga u yo'qligida javob berish.
Samimiy, qisqa va faqat o'zbek tilida javob bering.
"""
ai_model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- AI Logic ---
async def get_ai_response(prompt: str):
    try:
        response = await ai_model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "Kechirasiz, AI hozircha javob bera olmaydi. 😔"

# --- Render Port Binding ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def main():
    # 1. Initialize Bots inside main() to avoid loop errors
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    if STRING_SESSION:
        userbot = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION, in_memory=True)
    else:
        userbot = Client("my_account", api_id=API_ID, api_hash=API_HASH)

    # --- Bot Handlers ---
    @dp.message(Command("start"))
    async def start_handler(message: types.Message):
        await message.answer("Salom! Men Render-da ishlayotgan aqlli botman. 🚀")

    @dp.message(F.text)
    async def bot_chat_handler(message: types.Message):
        logger.info(f"Bot: {message.text[:50]}")
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        response = await get_ai_response(message.text)
        try:
            await message.answer(response, parse_mode="Markdown")
        except:
            await message.answer(response)

    # --- UserBot Handlers ---
    @userbot.on_message(filters.private & ~filters.me)
    async def userbot_auto_reply(client, message):
        logger.info(f"UserBot: {message.text[:50]}")
        response = await get_ai_response(message.text)
        if response:
            try:
                await message.reply(f"🤖 (AI Assistant):\n\n{response}", parse_mode="markdown")
            except:
                await message.reply(f"🤖 (AI Assistant):\n\n{response}")

    # --- Startup ---
    await userbot.start()
    logger.info("UserBot started.")
    
    try:
        print("Bot polling boshlanmoqda (v2.0)...")
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await userbot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
