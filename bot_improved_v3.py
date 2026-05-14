import os
import logging
import asyncio
import aiohttp
import io
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# تحميل الإعدادات
load_dotenv()

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# المتغيرات البيئية
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

# معلومات المطور
DEVELOPER_NAME = "علي حسين"
DEVELOPER_USER = "@alw_sh313"
DEVELOPER_LINK = "https://t.me/alw_sh313"

class AIBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN)
        self.dp = Dispatcher()
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        # استخدام نموذج مستقر وسريع جداً
        self.image_api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        self.setup_handlers()

    def get_main_keyboard(self):
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 ابدأ المحادثة", callback_data="start_chat"),
                InlineKeyboardButton(text="🎨 توليد صورة", callback_data="generate_image")
            ],
            [
                InlineKeyboardButton(text="👨‍💻 المطور", url=DEVELOPER_LINK),
                InlineKeyboardButton(text="❓ تعليمات", callback_data="how_to_use")
            ]
        ])

    def setup_handlers(self):
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            welcome_text = (
                f"🌟 **أهلاً بك في بوت الذكاء الاصطناعي!**\n\n"
                f"أنا مساعدك الذكي، جاهز للإجابة على أسئلتك وتوليد صور إبداعية لك.\n\n"
                f"👤 **المطور:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})\n"
                f"━━━━━━━━━━━━━━━\n"
                f"استخدم الأزرار أدناه للتحكم 👇"
            )
            await message.answer(welcome_text, parse_mode="Markdown", reply_markup=self.get_main_keyboard(), disable_web_page_preview=True)

        @self.dp.message(Command("draw"))
        async def cmd_draw(message: Message):
            prompt = message.text.replace("/draw", "").strip()
            if not prompt:
                await message.answer("⚠️ يرجى كتابة وصف للصورة بعد الأمر. \nمثال: `/draw قطة في الفضاء`", parse_mode="Markdown")
                return
            
            status_msg = await message.answer("⏳ **جاري العمل على صورتك...**\nيرجى الانتظار قليلاً.")
            
            headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
            payload = {"inputs": prompt, "options": {"wait_for_model": True}}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.image_api_url, headers=headers, json=payload, timeout=60) as response:
                        if response.status == 200:
                            image_bytes = await response.read()
                            if len(image_bytes) < 1000: # التحقق من أن الملف ليس رسالة خطأ نصية
                                raise Exception("الصورة المستلمة غير صالحة.")
                                
                            photo = BufferedInputFile(image_bytes, filename="art.png")
                            await message.answer_photo(
                                photo, 
                                caption=f"✅ تم التوليد بنجاح!\n📝 الوصف: {prompt}\n\n👤 المطور: {DEVELOPER_USER}",
                                parse_mode="Markdown"
                            )
                            await status_msg.delete()
                        else:
                            error_data = await response.text()
                            logging.error(f"HF Error: {error_data}")
                            await status_msg.edit_text("❌ **عذراً، الخدمة مشغولة حالياً.**\nيرجى المحاولة مرة أخرى بعد قليل.")
            except Exception as e:
                logging.error(f"Draw Error: {e}")
                await status_msg.edit_text(f"❌ **حدث خطأ أثناء التوليد.**\nتأكد من صحة مفتاح API الخاص بـ Hugging Face.")

        @self.dp.message(F.text)
        async def chat_handler(message: Message):
            await self.bot.send_chat_action(message.chat.id, "typing")
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": f"أنت مساعد ذكي محترف. المطور هو {DEVELOPER_NAME}."},
                        {"role": "user", "content": message.text}
                    ],
                    model="llama-3.3-70b-versatile",
                )
                await message.answer(chat_completion.choices[0].message.content, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Chat Error: {e}")
                await message.answer("⚠️ عذراً، واجهت مشكلة في الرد.")

        @self.dp.callback_query(F.data == "generate_image")
        async def cb_draw(callback: types.CallbackQuery):
            await callback.message.answer("🎨 أرسل الأمر `/draw` متبوعاً بوصف الصورة التي تريدها.")
            await callback.answer()

        @self.dp.callback_query(F.data == "how_to_use")
        async def cb_help(callback: types.CallbackQuery):
            await callback.message.answer("💡 **طريقة الاستخدام:**\n1. للمحادثة: أرسل أي نص.\n2. للرسم: أرسل `/draw` + وصف الصورة.")
            await callback.answer()

        @self.dp.callback_query(F.data == "start_chat")
        async def cb_chat(callback: types.CallbackQuery):
            await callback.message.answer("💬 أنا جاهز، تفضل بإرسال سؤالك.")
            await callback.answer()

    async def start(self):
        await self.dp.start_polling(self.bot)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not HUGGINGFACE_API_KEY:
        print("❌ خطأ: تأكد من ضبط TELEGRAM_TOKEN و HUGGINGFACE_API_KEY")
    else:
        bot = AIBot()
        asyncio.run(bot.start())
