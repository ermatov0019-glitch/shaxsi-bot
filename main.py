import asyncio
import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
import google.generativeai as genai

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

# --- Render uchun oddiy HTTP Server (Threading bilan) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"Render uchun HTTP server {port}-portda ishga tushdi.")
    server.serve_forever()

# --- Gemini AI funksiyasi ---
async def get_ai_response(prompt: str):
    try:
        response = await model.generate_content_async(prompt)
        return response.text.replace("**", "*")
    except Exception as e:
        logging.error(f"AI error: {e}")
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
    # HTTP serverni alohida oqimda (thread) ishga tushiramiz
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    
    print("Bot polling boshlanmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
