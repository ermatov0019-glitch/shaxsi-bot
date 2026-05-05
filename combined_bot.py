import os
# IMPORTANT: Disable Pyrogram's sync wrappers before ANY other imports
os.environ["PYROGRAM_SYNC"] = "0"

import asyncio
import logging
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import google.generativeai as genai
from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode

# Load environment variables
load_dotenv()

# --- Config ---
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
    logger.info("UserBotni ishga tushirish (Oddiy bot olib tashlandi)...")
    
    if not STRING_SESSION:
        logger.error("STRING_SESSION kiritilmagan! Bot ishlay olmaydi.")
        return

    try:
        clean_api_id = int(str(API_ID).strip().replace("+", ""))
        userbot = Client(
            "my_account", 
            api_id=clean_api_id, 
            api_hash=API_HASH, 
            session_string=STRING_SESSION, 
            in_memory=True
        )
    except Exception as e:
        logger.error(f"UserBot Init Error: {e}")
        return

    @userbot.on_message(filters.private & filters.incoming)
    async def userbot_auto_reply(client, message):
        logger.info(f"Yangi xabar keldi: {message.text[:50] if message.text else 'rasm/video'}")
        if not message.text:
            return # faqat matnli xabarlarga javob beradi
            
        response = await get_ai_response(message.text)
        if response:
            try:
                await message.reply(f"🤖 (AI Assistant):\n\n{response}", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Reply Error: {e}")
                await message.reply(f"🤖 (AI Assistant):\n\n{response}")

    try:
        await userbot.start()
        logger.info("UserBot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda...")
        await idle()
    except Exception as e:
        logger.error(f"UserBot ishlashida xatolik: {e}")
    finally:
        await userbot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dastur to'xtatildi.")
    except Exception:
        logger.error("KRASH SODIR BO'LDI!")
        logger.error(traceback.format_exc())
