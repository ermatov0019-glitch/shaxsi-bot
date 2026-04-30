import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from dotenv import load_dotenv
import google.generativeai as genai

# Fayllarni yuklash uchun yordamchi funksiyalar (Sizning oldingi downloader kodingiz asosida)
import yt_dlp

# Sozlamalar
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Gemini sozlamalari
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# Logging
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Gemini AI funksiyasi ---
async def get_ai_response(prompt: str):
    try:
        response = await model.generate_content_async(prompt)
        return response.text.replace("**", "*") # Telegram Markdown uchun
    except Exception as e:
        logging.error(f"AI error: {e}")
        return "Kechirasiz, AI hozircha javob bera olmaydi. 😔"

# --- Media Downloader funksiyasi ---
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
    }
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return [ydl.prepare_filename(info)]
    except Exception as e:
        logging.error(f"Download error: {e}")
        return None

# --- Handlers ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n\nMen sizning **Universal Shaxsi Bot**ingizman.\n\n"
        "Menga:\n"
        "1. Har qanday savol bering (AI javob beradi).\n"
        "2. Video havolasini yuboring (yuklab beraman).\n"
        "3. Men sizning API ma'lumotlaringiz bilan ham ishlay olaman!"
    )

@dp.message(F.text.regexp(r"(https?://\S+)"))
async def link_handler(message: types.Message):
    url = message.text
    status = await message.answer("Media yuklanmoqda... ⏳")
    
    file_paths = await asyncio.to_thread(download_media, url)
    if file_paths:
        for path in file_paths:
            await message.answer_video(FSInputFile(path))
            os.remove(path)
        await status.delete()
    else:
        await status.edit_text("Kechirasiz, yuklashda xatolik yuz berdi. ❌")

@dp.message(F.text)
async def chat_handler(message: types.Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    response = await get_ai_response(message.text)
    await message.answer(response, parse_mode="Markdown")

async def main():
    print("Universal Shaxsi Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
