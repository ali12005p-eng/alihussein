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
        """إنشاء لوحة الأزرار الرئيسية"""
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
            welcome_text = (
                f"🌟 **أهلاً بك في عالم الذكاء الاصطناعي!**\n\n"
                f"أنا بوت متطور أعمل بمحركات **Groq** و **SDXL** لتقديم أفضل تجربة لك.\n\n"
                f"✨ **ماذا يمكنني أن أفعل؟**\n"
                f"├ 💬 أجيب على تساؤلاتك بذكاء فائق.\n"
                f"├ 🎨 أحول خيالك إلى صور واقعية.\n"
                f"└ ⚡ أستجيب لك بسرعة البرق.\n\n"
                f"👤 **المطور:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})\n"
                f"━━━━━━━━━━━━━━━\n"
                f"اختر من الأزرار أدناه للبدء 👇"
            )
            await message.answer(welcome_text, parse_mode="Markdown", reply_markup=self.get_main_keyboard(), disable_web_page_preview=True)

        @self.dp.callback_query(F.data == "how_to_use")
        async def callback_how_to_use(callback_query: types.CallbackQuery):
            help_text = (
                "📖 **دليل الاستخدام السريع:**\n\n"
                "1️⃣ **للمحادثة:** أرسل أي نص مباشرة وسأرد عليك فوراً.\n"
                "2️⃣ **للرسم:** استخدم الأمر `/draw` ثم اكتب وصف الصورة بالإنجليزية أو العربية.\n"
                "   *مثال:* `/draw رائد فضاء يركب خيلاً في المريخ`\n\n"
                "💡 **نصيحة:** كلما كان وصفك للصورة دقيقاً، كانت النتيجة أروع!"
            )
            await callback_query.message.answer(help_text, parse_mode="Markdown")
            await callback_query.answer()

        @self.dp.callback_query(F.data == "start_chat")
        async def callback_start_chat(callback_query: types.CallbackQuery):
            await callback_query.message.answer("🤖 **أنا جاهز لسماعك!** تفضل بإرسال سؤالك أو موضوع لنناقشه.")
            await callback_query.answer()

        @self.dp.callback_query(F.data == "generate_image")
        async def callback_generate_image(callback_query: types.CallbackQuery):
            await callback_query.message.answer("🎨 **وضع الإبداع:** أرسل `/draw` متبوعاً بوصفك لنحول الكلمات إلى فن!")
            await callback_query.answer()

        @self.dp.message(Command("draw"))
        async def cmd_draw(message: Message):
            prompt = message.text.replace("/draw", "").strip()
            if not prompt:
                await message.answer("⚠️ **عذراً!** يرجى كتابة وصف للصورة. \nمثال: `/draw منظر طبيعي خلاب`")
                return
            
            sent_msg = await message.answer("⏳ **جاري الإبداع...** \nنحن نستخدم محرك SDXL لتوليد صورتك.")
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.image_api_url,
                        headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                        json={"inputs": prompt}
                    ) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            caption = f"✅ **تم التوليد بنجاح!**\n📝 **الوصف:** {prompt}\n\n👤 **بواسطة:** {DEVELOPER_USER}"
                            await message.answer_photo(
                                BufferedInputFile(image_data, filename="ai_art.png"),
                                caption=caption,
                                parse_mode="Markdown"
                            )
                        elif response.status == 503:
                            await sent_msg.edit_text("😴 **الخادم يأخذ استراحة قصيرة!**\nالنموذج قيد التحميل، يرجى المحاولة بعد 30 ثانية.")
                        else:
                            await sent_msg.edit_text("❌ **عذراً، حدث خطأ فني.** حاول مرة أخرى لاحقاً.")
            except Exception as e:
                logging.error(f"Error: {e}")
                await sent_msg.edit_text("❌ **فشل الاتصال بالخادم.**")
            finally:
                await sent_msg.delete()

        @self.dp.message(F.text)
        async def chat_handler(message: Message):
            # إظهار حالة "يكتب الآن"
            await self.bot.send_chat_action(message.chat.id, "typing")
            
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": f"أنت مساعد ذكي محترف، تجيب باللغة العربية. المطور الخاص بك هو {DEVELOPER_NAME} وحسابه هو {DEVELOPER_USER}."},
                        {"role": "user", "content": message.text}
                    ],
                    model="llama-3.3-70b-versatile",
                )
                response = chat_completion.choices[0].message.content
                # إضافة توقيع بسيط في نهاية الردود الطويلة
                if len(response) > 200:
                    response += f"\n\n--- \n✨ بواسطة: {DEVELOPER_USER}"
                
                await message.answer(response, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Chat Error: {e}")
                await message.answer("⚠️ **عذراً، واجهت مشكلة في معالجة طلبك.**")

    async def start(self):
        await self.dp.start_polling(self.bot)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("❌ خطأ: تأكد من ضبط المتغيرات البيئية!")
    else:
        bot = AIBot()
        asyncio.run(bot.start())
