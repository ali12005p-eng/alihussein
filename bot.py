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

# معلومات المطور والبوت
BOT_NAME = "العملاق"
DEVELOPER_NAME = "علي حسين"
DEVELOPER_USER = "@alw_sh313"
DEVELOPER_rLINK = "https://t.me/alw_sh313"

class AIBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN)
        self.dp = Dispatcher()
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.image_api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
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
            ],
            [
                InlineKeyboardButton(text="📢 مشاركة العملاق", switch_inline_query="جرب بوت العملاق الذكي!")
            ]
        ])

    def setup_handlers(self):
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            welcome_text = (
                f"🚀 **أهلاً بك، أنا {BOT_NAME}!**\n\n"
                f"أنا أذكى بوت في التيليجرام، أعمل بمحركات **Groq** و **SDXL**.\n"
                f"يمكنني التفاعل معكم في المجموعات عند مناداتي بـ '**{BOT_NAME}**' أو '**بوت**'.\n\n"
                f"👤 **المطور:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})\n"
                f"━━━━━━━━━━━━━━━\n"
                f"اختر من الأزرار أدناه للبدء 👇"
            )
            await message.answer(welcome_text, parse_mode="Markdown", reply_markup=self.get_main_keyboard(), disable_web_page_preview=True)

        @self.dp.message(Command("draw"))
        async def cmd_draw(message: Message):
            prompt = message.text.replace("/draw", "").strip()
            if not prompt:
                await message.reply(f"⚠️ يرجى كتابة وصف للصورة. مثال: `/draw {BOT_NAME} في الفضاء`", parse_mode="Markdown")
                return
            
            sent_msg = await message.reply("⏳ **جاري الإبداع...**")
            
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
                            caption = f"✅ **تم التوليد بنجاح!**\n👤 **بواسطة:** {message.from_user.first_name}\n🤖 **البوت:** {BOT_NAME}\n🎨 **المطور:** {DEVELOPER_USER}"
                            await message.answer_photo(
                                BufferedInputFile(image_data, filename="ai_art.png"),
                                caption=caption,
                                parse_mode="Markdown"
                            )
                        else:
                            await message.reply("❌ **عذراً، الخدمة مشغولة حالياً.**")
            except Exception as e:
                logging.error(f"Draw Error: {e}")
                await message.reply("❌ **حدث خطأ أثناء توليد الصورة.**")
            finally:
                await sent_msg.delete()

        @self.dp.message(F.text)
        async def chat_handler(message: Message):
            text = message.text.strip()
            is_private = message.chat.type == "private"
            
            # التحقق من المناداة
            mentions_name = text.startswith(BOT_NAME)
            mentions_bot = text.startswith("بوت")
            is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == (await self.bot.get_me()).id
            
            # التحقق إذا كان السؤال عن المطور
            dev_keywords = ["مطور", "المطور", "صانعك", "من صنعك", "علي حسين", "صاحب البوت"]
            is_asking_about_dev = any(word in text for word in dev_keywords)

            if is_private or mentions_name or mentions_bot or is_reply_to_bot:
                # إذا كان السؤال عن المطور، نرد مباشرة لتجنب أخطاء الـ AI
                if is_asking_about_dev:
                    dev_info = (
                        f"👤 **معلومات المطور:**\n\n"
                        f"مطور هذا البوت هو المبدع **{DEVELOPER_NAME}**.\n"
                        f"يمكنك التواصل معه عبر حسابه الرسمي: {DEVELOPER_USER}\n"
                        f"أو عبر الرابط: {DEVELOPER_rLINK}
                    )
                    await message.reply(dev_info, parse_mode="Markdown")
                    return

                await self.bot.send_chat_action(message.chat.id, "typing")
                
                user_input = text
                if mentions_name: user_input = user_input.replace(BOT_NAME, "", 1).strip()
                elif mentions_bot: user_input = user_input.replace("بوت", "", 1).strip()
                
                if not user_input and (mentions_name or mentions_bot):
                    await message.reply(f"نعم يا غالي، **{BOT_NAME}** معك! كيف يمكنني مساعدتك؟")
                    return

                try:
                    chat_completion = self.groq_client.chat.completions.create(
                        messages=[
                            {
                                "role": "system", 
                                "content": f"أنت مساعد ذكي واسمك هو {BOT_NAME}. المطور الخاص بك هو {DEVELOPER_NAME} وحسابه {DEVELOPER_USER}. "
                                           f"أجب بأسلوب فخم وذكي باللغة العربية."
                            },
                            {"role": "user", "content": user_input}
                        ],
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
                        max_tokens=1024
                    )
                    await message.reply(chat_completion.choices[0].message.content, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Chat Error: {e}")
                    # محاولة الرد بدون تنسيق Markdown إذا فشل الأول
                    try:
                        await message.reply(chat_completion.choices[0].message.content)
                    except:
                        await message.reply("⚠️ عذراً، واجهت مشكلة بسيطة في التفكير. حاول مرة أخرى!")

        @self.dp.callback_query(F.data == "how_to_use")
        async def cb_help(callback: types.CallbackQuery):
            await callback.message.answer(f"📖 **دليل استخدام {BOT_NAME}:**\n- في الخاص: أرسل أي سؤال مباشرة.\n- في المجموعات: ابدأ رسالتك بكلمة '{BOT_NAME}' أو 'بوت' أو رد على رسالتي.")
            await callback.answer()

        @self.dp.callback_query(F.data == "start_chat")
        async def cb_chat(callback: types.CallbackQuery):
            await callback.message.answer(f"🤖 **{BOT_NAME}** جاهز لخدمتك!")
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
