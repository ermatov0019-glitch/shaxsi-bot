import asyncio
import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from pyrogram import Client, filters, idle
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION") # For hosting

# --- AI Setup ---
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-flash-latest')

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Aiogram Bot Setup ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Pyrogram UserBot Setup ---
if STRING_SESSION:
    userbot = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    logger.info("STRING_SESSION topildi, UserBot string session orqali ishga tushadi.")
else:
    userbot = Client("my_account", api_id=API_ID, api_hash=API_HASH)
    logger.warning("DIQQAT: STRING_SESSION topilmadi! UserBot fayl orqali ishlashga harakat qiladi (hostingda bu xatolik berishi mumkin).")

# --- Render Port Binding (HTTP Server) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server started on port {port}")
    server.serve_forever()

# --- AI Logic ---
async def get_ai_response(prompt: str, is_userbot=False):
    try:
        prefix = "Siz foydalanuvchining shaxsiy yordamchisiz. Barcha savollarga faqat o'zbek tilida, samimiy javob bering." if is_userbot else ""
        full_prompt = f"{prefix} Savol: {prompt}" if prefix else prompt
        
        response = await ai_model.generate_content_async(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "Kechirasiz, AI hozircha javob bera olmaydi. 😔"

# --- Bot Handlers ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Men Render-da ishlayotgan aqlli botman. 🚀")

@dp.message(F.text)
async def bot_chat_handler(message: types.Message):
    logger.info(f"Botga xabar keldi: {message.text[:50]}...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    response = await get_ai_response(message.text)
    logger.info(f"Bot AI javobi: {response[:50]}...")
    try:
        await message.answer(response, parse_mode="Markdown")
    except Exception:
        await message.answer(response)

# --- UserBot Handlers ---
@userbot.on_message(filters.private & ~filters.me)
async def userbot_auto_reply(client, message):
    logger.info(f"UserBot received: {message.text[:50]}...")
    response = await get_ai_response(message.text, is_userbot=True)
    if response:
        try:
            await message.reply(f"🤖 (AI Assistant):\n\n{response}", parse_mode="markdown")
        except Exception:
            await message.reply(f"🤖 (AI Assistant):\n\n{response}")

# --- Main Runner ---
async def main():
    # Start UserBot
    await userbot.start()
    logger.info("UserBot started.")
    
    # Start Aiogram Polling (this keeps the process alive)
    try:
        print("Bot polling boshlanmoqda (Combined Version)...")
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await userbot.stop()

if __name__ == "__main__":
    # 1. Start HTTP Server immediately to satisfy Render
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
