import os
import logging
import asyncio
import aiohttp
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
        self.image_api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        self.setup_handlers()

    def get_main_keyboard(self):
        """نفس لوحة الأزرار التي أعجبتك في النسخة الثانية"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 ابدأ المحادثة", callback_data="start_chat"),
                InlineKeyboardButton(text="🎨 توليد صورة", callback_data="generate_image")
            ],
            [
                InlineKeyboardButton(text="👨‍💻 المطور", url=DEVELOPER_LINK),
                InlineKeyboardButton(text="❓ تعليمات", callback_data="how_to_use")
            ],
            [
                InlineKeyboardButton(text="📢 مشاركة البوت", switch_inline_query="جرب هذا البوت الرهيب!")
            ]
        ])

    def setup_handlers(self):
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            # نفس رسالة الترحيب التي أعجبتك
            welcome_text = (
                f"🌟 **أهلاً بك في عالم الذكاء الاصطناعي!**\n\n"
                f"أنا بوت متطور أعمل بمحركات **Groq** و **SDXL** لتقديم أفضل تجربة لك.\n\n"
                f"✨ **ماذا يمكنني أن أفعل؟**\n"
                f"├ 💬 أجيب على تساؤلاتك بذكاء فائق.\n"
                f"🎨 أحول خيالك إلى صور واقعية.\n"
                f"└ ⚡ أستجيب لك بسرعة البرق.\n\n"
                f"👤 **المطور:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})\n"
                f"━━━━━━━━━━━━━━━\n"
                f"اختر من الأزرار أدناه للبدء 👇"
            )
            await message.answer(welcome_text, parse_mode="Markdown", reply_markup=self.get_main_keyboard(), disable_web_page_preview=True)

        @self.dp.message(Command("draw"))
        async def cmd_draw(message: Message):
            prompt = message.text.replace("/draw", "").strip()
            if not prompt:
                await message.answer("⚠️ **عذراً!** يرجى كتابة وصف للصورة. \nمثال: `/draw قطة في الفضاء`", parse_mode="Markdown")
                return
            
            sent_msg = await message.answer("⏳ **جاري الإبداع...**")
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.image_api_url,
                        headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                        json={"inputs": prompt, "options": {"wait_for_model": True}},
                        timeout=60
                    ) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            caption = f"✅ **تم التوليد بنجاح!**\n📝 **الوصف:** {prompt}\n\n👤 **بواسطة:** {DEVELOPER_USER}"
                            await message.answer_photo(
                                BufferedInputFile(image_data, filename="ai_art.png"),
                                caption=caption,
                                parse_mode="Markdown"
                            )
                        else:
                            await message.answer("❌ **عذراً، الخدمة مشغولة حالياً.** حاول مرة أخرى.")
            except Exception as e:
                logging.error(f"Draw Error: {e}")
                await message.answer("❌ **حدث خطأ أثناء توليد الصورة.**")
            finally:
                await sent_msg.delete()

        @self.dp.message(F.text)
        async def chat_handler(message: Message):
            await self.bot.send_chat_action(message.chat.id, "typing")
            
            try:
                # تحسين الـ System Prompt ليكون أكثر قدرة على الشرح المفصل
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": f"أنت مساعد ذكي خبير ومحترف جداً. المطور الخاص بك هو {DEVELOPER_NAME} ({DEVELOPER_USER}). "
                                       f"قدم شروحات وافية ومفصلة ودقيقة لكل ما يطلبه المستخدم باللغة العربية بأسلوب تعليمي رائع."
                        },
                        {"role": "user", "content": message.text}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.6, # درجة حرارة متوازنة للدقة والإبداع
                    max_tokens=2048 # زيادة عدد التوكنات للسماح بالشروحات الطويلة
                )
                
                response = chat_completion.choices[0].message.content
                
                # معالجة النصوص الطويلة جداً لتيليجرام (الحد الأقصى 4096 حرف)
                if len(response) > 4000:
                    for i in range(0, len(response), 4000):
                        await message.answer(response[i:i+4000])
                else:
                    # محاولة الإرسال بتنسيق Markdown، وإذا فشل نرسله كنص عادي لتجنب الخطأ
                    try:
                        await message.answer(response, parse_mode="Markdown")
                    except:
                        await message.answer(response)
                        
            except Exception as e:
                logging.error(f"Chat Error: {e}")
                await message.answer("⚠️ **عذراً، واجهت مشكلة في معالجة طلبك.** يرجى المحاولة مرة أخرى.")

        # معالجات الأزرار (نفس النسخة الثانية)
        @self.dp.callback_query(F.data == "how_to_use")
        async def cb_help(callback: types.CallbackQuery):
            await callback.message.answer("📖 **دليل الاستخدام:**\nأرسل أي سؤال للشرح، أو استخدم `/draw` للرسم.")
            await callback.answer()

        @self.dp.callback_query(F.data == "start_chat")
        async def cb_chat(callback: types.CallbackQuery):
            await callback.message.answer("🤖 أنا جاهز! تفضل بإرسال سؤالك وسأقوم بشرحه لك بالتفصيل.")
            await callback.answer()

        @self.dp.callback_query(F.data == "generate_image")
        async def cb_draw(callback: types.CallbackQuery):
            await callback.message.answer("🎨 أرسل `/draw` متبوعاً بوصف الصورة.")
            await callback.answer()

    async def start(self):
        await self.dp.start_polling(self.bot)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("❌ خطأ في الإعدادات!")
    else:
        bot = AIBot()
        asyncio.run(bot.start())
