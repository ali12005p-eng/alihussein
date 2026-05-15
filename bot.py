import os
import logging
import asyncio
import aiohttp
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from dotenv import load_dotenv

# تحميل الإعدادات
load_dotenv()

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)

# المتغيرات البيئية
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", "0"))

# معلومات المطور والبوت
BOT_NAME = "العملاق"
DEVELOPER_NAME = "علي حسين"
DEVELOPER_USER = "@alw_sh313"
DEVELOPER_LINK = "https://t.me/alw_sh313"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)
IMAGE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

# --- لوحة الأزرار (النسخة القديمة التي أعجبتك) ---
def get_main_keyboard():
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

# --- أوامر المطور (تعمل فقط للايدي الخاص بك) ---
@dp.message(Command("اذاعة"), F.from_user.id == DEVELOPER_ID)
async def cmd_broadcast(message: Message, command: CommandObject):
    text = command.args
    if not text: return await message.reply("⚠️ أرسل النص مع الأمر.")
    await message.reply("🚀 ميزة الإذاعة تتطلب قاعدة بيانات للمجموعات، سيتم تطويرها قريباً.")

@dp.message(Command("احصائيات"), F.from_user.id == DEVELOPER_ID)
async def cmd_stats(message: Message):
    await message.reply(f"📊 **إحصائيات العملاق:**\n\n👤 المطور: {DEVELOPER_NAME}\n🆔 ايديك: `{DEVELOPER_ID}`\n🤖 الحالة: متصل")

# --- ترحيب المجموعات وتنبيه المطور ---
@dp.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated):
    if event.new_chat_member.status in ["member", "administrator"]:
        # رسالة ترحيب في المجموعة
        welcome_group = (
            f"👋 **أهلاً بكم! أنا {BOT_NAME}**\n\n"
            f"لقد تم إضافتي للمجموعة بنجاح. لكي أعمل بكامل قوتي:\n"
            f"1️⃣ ارفعني **مشرفاً** في المجموعة.\n"
            f"2️⃣ نادني بكلمة '**{BOT_NAME}**' أو '**بوت**'.\n"
            f"3️⃣ استخدم `/draw` للرسم الذكي.\n\n"
            f"👤 المطور: {DEVELOPER_USER}"
        )
        await bot.send_message(event.chat.id, welcome_group, parse_mode="Markdown")
        
        # تنبيه المطور
        try:
            chat_link = await event.chat.export_invite_link() if event.chat.username is None else f"https://t.me/{event.chat.username}"
        except: chat_link = "لا يمكن جلب الرابط (ارفعني مشرفاً)"
        
        alert_text = (
            f"🔔 **تنبيه تفعيل جديد!**\n\n"
            f"تم إضافة {BOT_NAME} لمجموعة جديدة:\n"
            f"🏷️ الاسم: {event.chat.title}\n"
            f"🆔 الايدي: `{event.chat.id}`\n"
            f"🔗 الرابط: {chat_link}"
        )
        await bot.send_message(DEVELOPER_ID, alert_text, parse_mode="Markdown")

# --- الأوامر العامة (رسالة الستارت القديمة) ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        f"🚀 **أهلاً بك، أنا {BOT_NAME}!**\n\n"
        f"أنا أذكى بوت في التيليجرام، أعمل بمحركات **Groq** و **SDXL**.\n"
        f"يمكنني التفاعل معكم في المجموعات عند مناداتي بـ '**{BOT_NAME}**' أو '**بوت**'.\n\n"
        f"👤 **المطور:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر من الأزرار أدناه للبدء 👇"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard(), disable_web_page_preview=True)

@dp.message(Command("draw"))
async def cmd_draw(message: Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        return await message.reply(f"⚠️ يرجى كتابة وصف للصورة. مثال: `/draw {BOT_NAME} في الفضاء`", parse_mode="Markdown")
    
    sent_msg = await message.reply("⏳ **جاري الإبداع...**")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(IMAGE_API_URL, headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}, json={"inputs": prompt, "options": {"wait_for_model": True}}, timeout=60) as response:
                if response.status == 200:
                    image_data = await response.read()
                    await message.answer_photo(BufferedInputFile(image_data, filename="ai_art.png"), caption=f"✅ تم التوليد بواسطة {BOT_NAME}\n🎨 المطور: {DEVELOPER_USER}")
                else: await message.reply("❌ الخدمة مشغولة حالياً.")
    except: await message.reply("❌ حدث خطأ أثناء الرسم.")
    finally: await sent_msg.delete()

@dp.message(F.text)
async def chat_handler(message: Message):
    text = message.text.strip()
    is_private = message.chat.type == "private"
    mentions_name = text.startswith(BOT_NAME)
    mentions_bot = text.startswith("بوت")
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == (await bot.get_me()).id
    
    if any(word in text for word in ["مطور", "المطور", "علي حسين"]):
        await message.reply(f"👤 مطوري هو المبدع **{DEVELOPER_NAME}** ({DEVELOPER_USER}).")
        return

    if is_private or mentions_name or mentions_bot or is_reply_to_bot:
        await bot.send_chat_action(message.chat.id, "typing")
        user_input = text.replace(BOT_NAME, "").replace("بوت", "", 1).strip()
        if not user_input:
            await message.reply(f"نعم يا غالي، **{BOT_NAME}** معك! كيف أقدر أساعدك؟")
            return

        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": f"أنت {BOT_NAME}، مساعد ذكي مطورك {DEVELOPER_NAME}."}, {"role": "user", "content": user_input}],
                model="llama-3.3-70b-versatile",
            )
            await message.reply(chat_completion.choices[0].message.content, parse_mode="Markdown")
        except: await message.reply("⚠️ عذراً، واجهت مشكلة في التفكير.")

# --- تشغيل ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
