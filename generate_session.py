import asyncio
import os
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

async def generate():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    
    if not api_id or not api_hash:
        print("XATO: .env faylida API_ID va API_HASH bo'lishi shart!")
        return

    async with Client("session_generator", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
        session_string = await app.export_session_string()
        print("\n" + "="*50)
        print("SIZNING STRING SESSION:")
        print("="*50)
        print(session_string)
        print("="*50)
        print("\nUshbu kodni nusxalab oling va Render-da 'STRING_SESSION' o'zgaruvchisiga qiymat qilib bering.")

if __name__ == "__main__":
    asyncio.run(generate())
