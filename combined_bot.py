import os
# IMPORTANT: Disable Pyrogram's sync wrappers before ANY other imports
os.environ["PYROGRAM_SYNC"] = "0"

import asyncio
import logging
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from groq import AsyncGroq

# Load environment variables
load_dotenv()

# --- Config ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    SYSTEM_PROMPT = "Siz foydalanuvchining shaxsiy yordamchisiz. Samimiy va faqat o'zbek tilida javob bering."
    groq_api_key_clean = (GROQ_API_KEY or "").strip()
    groq_client = AsyncGroq(api_key=groq_api_key_clean)
    setup_error = None
except Exception as e:
    logger.error(f"AI Setup Error: {e}")
    groq_client = None
    setup_error = str(e)

async def get_ai_response(prompt: str):
    if not groq_client:
        return f"AI ishlamayapti. Sababi (Setup Error): {setup_error} | GROQ_API_KEY tekshiring."
    try:
        completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Logic Error: {e}")
        return f"Xatolik yuz berdi: {str(e)}"

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
        
    from pyrogram import Client, filters, idle
    from pyrogram.enums import ParseMode

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
