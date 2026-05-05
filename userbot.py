import asyncio
import os
import logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from dotenv import load_dotenv
import google.generativeai as genai

# Sozlamalarni yuklash
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini AI sozlamalari
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Logging
logging.basicConfig(level=logging.INFO)

# UserBot klientini yaratish
app = Client("my_account", api_id=API_ID, api_hash=API_HASH)

async def get_ai_response(prompt: str):
    try:
        # AI ga o'zbekcha javob berish haqida ko'rsatma beramiz
        full_prompt = f"Siz foydalanuvchining shaxsiy yordamchisiz. Barcha savollarga faqat o'zbek tilida, samimiy va tushunarli javob bering. Savol: {prompt}"
        response = await model.generate_content_async(full_prompt)
        return response.text
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return None

@app.on_message(filters.private & ~filters.me)
async def auto_reply(client, message):
    """
    Lichkaga kelgan xabarlarga javob berish
    """
    print(f"Yangi xabar: {message.text}")
    
    # AI dan javob olish
    ai_response = await get_ai_response(message.text)
    
    if ai_response:
        # AI javobini yuborish
        await message.reply(f"🤖 (AI Assistant):\n\n{ai_response}")

print("UserBot ishga tushmoqda...")
app.run()
