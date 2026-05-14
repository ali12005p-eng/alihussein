import os
import logging
import asyncio
import aiohttp
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# تحميل الإعدادات من ملف .env
load_dotenv()

# إعداد التسجيل (Logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# قراءة المتغيرات البيئية
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY") # تم تغيير HF_TOKEN إلى HUGGINGFACE_API_KEY للوضوح

# تعريف فئات الأخطاء المخصصة
class MissingEnvironmentVariableError(Exception):
    """يتم إطلاق هذا الخطأ عند فقدان متغير بيئة أساسي."""
    pass

class ImageGenerationError(Exception):
    """يتم إطلاق هذا الخطأ عند فشل عملية توليد الصورة."""
    pass

class AIBot:
    def __init__(self):
        if not TELEGRAM_TOKEN:
            raise MissingEnvironmentVariableError("TELEGRAM_TOKEN غير موجود. يرجى إضافته إلى ملف .env")
        if not GROQ_API_KEY:
            raise MissingEnvironmentVariableError("GROQ_API_KEY غير موجود. يرجى إضافته إلى ملف .env")
        # HUGGINGFACE_API_KEY اختياري لميزة الرسم

        self.bot = Bot(token=TELEGRAM_TOKEN)
        self.dp = Dispatcher()
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.image_generation_api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0" # استخدام نموذج SDXL
        self.setup_handlers()

    def setup_handlers(self):
        # معالج أمر /start المحسن
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ابدأ المحادثة 💬", callback_data="start_chat")],
                [InlineKeyboardButton(text="كيف أستخدم البوت؟ ❓", callback_data="how_to_use")],
                [InlineKeyboardButton(text="توليد صورة 🎨", callback_data="generate_image")]
            ])
            await message.answer(
                "🚀 **أهلاً بك في بوت الذكاء الاصطناعي المتطور!**\n\n"
                "أنا هنا لمساعدتك في مهامك اليومية، سواء كانت محادثة سريعة أو توليد صور إبداعية.\n"
                "**الميزات المتاحة:**\n"
                "💬 **محادثة فورية:** استخدم محرك **Groq** فائق السرعة للإجابة على أسئلتك.\n"
                "🎨 **توليد الصور:** أنشئ صوراً مذهلة من وصفك النصي.\n\n"
                "اختر من الخيارات أدناه للبدء:",
                parse_mode="Markdown",
                reply_markup=keyboard
            )

        # معالج استدعاءات الأزرار (Callback Queries)
        @self.dp.callback_query(F.data == "start_chat")
        async def callback_start_chat(callback_query: types.CallbackQuery):
            await callback_query.message.answer("أهلاً بك في وضع المحادثة! أرسل لي سؤالك وسأجيبك فوراً.")
            await callback_query.answer() # يجب الرد على الـ callback_query

        @self.dp.callback_query(F.data == "how_to_use")
        async def callback_how_to_use(callback_query: types.CallbackQuery):
            await callback_query.message.answer(
                "**كيف تستخدم البوت؟**\n\n"
                "💬 **للمحادثة:** ببساطة أرسل لي أي سؤال أو نص، وسأقوم بالرد عليك.\n"
                "🎨 **لتوليد الصور:** استخدم الأمر `/draw` متبوعاً بوصف الصورة التي تريدها. مثال: `/draw قطة فضائية ترتدي خوذة`\n"
                "استمتع باستخدام البوت!"
            )
            await callback_query.answer()

        @self.dp.callback_query(F.data == "generate_image")
        async def callback_generate_image(callback_query: types.CallbackQuery):
            await callback_query.message.answer("أهلاً بك في وضع توليد الصور! يرجى استخدام الأمر `/draw` متبوعاً بوصف الصورة التي تريدها.")
            await callback_query.answer()

        # معالج أمر /draw المحسن
        @self.dp.message(Command("draw"))
        async def cmd_draw(message: Message):
            if not HUGGINGFACE_API_KEY:
                await message.answer("❌ لا يمكن توليد الصور حالياً. يرجى تزويد البوت بمفتاح HUGGINGFACE_API_KEY.")
                return

            prompt = message.text.replace("/draw", "").strip()
            if not prompt:
                await message.answer("❌ يرجى كتابة وصف للصورة بعد الأمر `/draw`. مثال: `/draw قطة فضائية`")
                return
            
            sent_msg = await message.answer("🎨 جاري توليد الصورة... قد يستغرق الأمر بعض الوقت.")
            logging.info(f"بدء توليد صورة للوصف: {prompt}")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.image_generation_api_url,
                        headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                        json={"inputs": prompt}
                    ) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            await message.answer_photo(BufferedInputFile(image_data, filename="generated_image.png"))
                            logging.info(f"تم توليد الصورة بنجاح للوصف: {prompt}")
                        elif response.status == 503:
                            # Hugging Face Inference API returns 503 when model is loading
                            await sent_msg.edit_text("⏳ النموذج قيد التحميل حالياً. يرجى المحاولة مرة أخرى بعد قليل.")
                            logging.warning(f"نموذج توليد الصور قيد التحميل (503) للوصف: {prompt}")
                        else:
                            error_detail = await response.json() if response.headers.get('Content-Type') == 'application/json' else await response.text()
                            raise ImageGenerationError(f"فشل توليد الصورة: {response.status} - {error_detail}")
            except ImageGenerationError as e:
                await sent_msg.edit_text(f"❌ {e}")
                logging.error(f"خطأ في توليد الصورة: {e}")
            except aiohttp.ClientError as e:
                await sent_msg.edit_text(f"❌ خطأ في الاتصال بخدمة توليد الصور: {e}")
                logging.error(f"خطأ في الاتصال بـ Hugging Face API: {e}")
            except Exception as e:
                await sent_msg.edit_text(f"❌ حدث خطأ غير متوقع أثناء توليد الصورة: {e}")
                logging.error(f"خطأ غير متوقع أثناء توليد الصورة: {e}", exc_info=True)
            finally:
                await sent_msg.delete() # حذف رسالة 'جاري التوليد...' بعد الانتهاء

        # معالج المحادثة النصية
        @self.dp.message(F.text)
        async def chat_handler(message: Message):
            await self.bot.send_chat_action(message.chat.id, "typing")
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "أنت مساعد ذكي محترف وسريع جداً، تجيب باللغة العربية بأسلوب رائع ومختصر قدر الإمكان."}, # تحسين توجيه النظام
                        {"role": "user", "content": message.text,}
                    ],
                    model="llama-3.3-70b-versatile", # استخدام النموذج المحدد
                    temperature=0.7, # إضافة درجة حرارة للتحكم بالإبداع
                    max_tokens=1024 # تحديد أقصى عدد للتوكنات
                )
                response_text = chat_completion.choices[0].message.content
                await message.answer(response_text, parse_mode="Markdown")
                logging.info(f"تم الرد على المحادثة بنجاح للرسالة: {message.text[:50]}...")
            except Exception as e:
                await message.answer(f"❌ حدث خطأ أثناء المحادثة: {str(e)}")
                logging.error(f"خطأ في معالج المحادثة: {e}", exc_info=True)

    async def start(self):
        logging.info("بدء تشغيل بوت Groq AI...")
        try:
            await self.dp.start_polling(self.bot, allowed_updates=self.dp.resolve_used_update_types()) # تحديد أنواع التحديثات المسموح بها
        except Exception as e:
            logging.critical(f"فشل في بدء تشغيل البوت: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        bot_instance = AIBot()
        asyncio.run(bot_instance.start())
    except MissingEnvironmentVariableError as e:
        logging.critical(f"خطأ في الإعداد: {e}")
    except Exception as e:
        logging.critical(f"خطأ فادح في التطبيق: {e}", exc_info=True)
