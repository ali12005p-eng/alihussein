import asyncio
import os
import logging
from bot import AIBot
from dotenv import load_dotenv

# تحميل المتغيرات
load_dotenv()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # التحقق من المتغيرات
    if not os.environ.get("TELEGRAM_TOKEN"):
        logging.error("TELEGRAM_TOKEN is missing!")
    
    if not os.environ.get("GROQ_API_KEY"):
        logging.error("GROQ_API_KEY is missing!")

    try:
        bot_instance = AIBot()
        asyncio.run(bot_instance.start())
    except Exception as e:
        logging.error(f"Error: {e}")
