import asyncio
import os
import logging
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
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

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- AI Setup ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    SYSTEM_PROMPT = "Siz foydalanuvchining shaxsiy yordamchisiz. Samimiy va faqat o'zbek tilida javob bering."
    ai_model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
except Exception as e:
    logger.error(f"AI Setup Error: {e}")
    ai_model = None

async def get_ai_response(prompt: str):
    if not ai_model:
        return "AI hozircha ishlamayapti. 😔"
    try:
        response = await ai_model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"AI Logic Error: {e}")
        return "Xatolik yuz berdi. 😔"

# --- Health Check ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def main():
    logger.info("Botni ishga tushirish (Python 3.14 fix)...")
    
    # 1. Initialize Aiogram
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # 2. IMPORTANT: Import Pyrogram INSIDE main() to avoid loop errors
    from pyrogram import Client, filters
    
    userbot = None
    if STRING_SESSION:
        try:
            userbot = Client(
                "my_account", 
                api_id=API_ID, 
                api_hash=API_HASH, 
                session_string=STRING_SESSION, 
                in_memory=True
            )
            logger.info("UserBot konfiguratsiyasi tayyor.")
        except Exception as e:
            logger.error(f"UserBot Init Error: {e}")

    # --- Aiogram Handlers ---
    @dp.message(Command("start"))
    async def start_handler(message: types.Message):
        await message.answer("Salom! Men Render-da ishlayotgan aqlli botman. 🚀")

    @dp.message(F.text)
    async def bot_chat_handler(message: types.Message):
        response = await get_ai_response(message.text)
        try:
            await message.answer(response, parse_mode="Markdown")
        except:
            await message.answer(response)

    # --- Pyrogram Handlers (Registered manually) ---
    if userbot:
        @userbot.on_message(filters.private & ~filters.me)
        async def userbot_auto_reply(client, message):
            response = await get_ai_response(message.text)
            if response:
                try:
                    await message.reply(f"🤖 (AI Assistant):\n\n{response}", parse_mode="markdown")
                except:
                    await message.reply(f"🤖 (AI Assistant):\n\n{response}")

    # --- Start ---
    if userbot:
        try:
            await userbot.start()
            logger.info("UserBot muvaffaqiyatli ishga tushdi.")
        except Exception as e:
            logger.error(f"UserBot Start Error: {e}")

    try:
        logger.info("Aiogram polling boshlanmoqda...")
        await dp.start_polling(bot, skip_updates=True)
    finally:
        if userbot:
            await userbot.stop()

if __name__ == "__main__":
    # Start HTTP server immediately
    threading.Thread(target=run_http_server, daemon=True).start()
    
    try:
        asyncio.run(main())
    except Exception:
        logger.error("KRASH SODIR BO'LDI!")
        logger.error(traceback.format_exc())
