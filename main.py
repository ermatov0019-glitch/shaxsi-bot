import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import google.generativeai as genai
from aiohttp import web

# Sozlamalar
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini sozlamalari
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# Logging
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Render uchun qalbaki web server ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render beradigan PORT-ni ishlatamiz, agar yo'q bo'lsa 8080
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server {port}-portda ishga tushdi.")

# --- Gemini AI funksiyasi ---
async def get_ai_response(prompt: str):
    try:
        response = await model.generate_content_async(prompt)
        return response.text.replace("**", "*")
    except Exception as e:
        logging.error(f"AI error: {e}")
        if "403" in str(e):
            return "Xatolik: API kalit bloklangan. Yangi kalit qo'ying! 🔑"
        return "Kechirasiz, AI hozircha javob bera olmaydi. 😔"

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Men Render-da ishlayotgan aqlli botman. 🚀")

@dp.message(F.text)
async def chat_handler(message: types.Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    response = await get_ai_response(message.text)
    await message.answer(response, parse_mode="Markdown")

async def main():
    # Bir vaqtda ham botni, ham web serverni ishga tushiramiz
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
