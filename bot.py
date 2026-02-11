#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
from telebot import TeleBot, types
import yt_dlp
from dotenv import load_dotenv
import subprocess

# =======================
# تحميل التوكن من .env
# =======================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في ملف .env")

bot = TeleBot(TOKEN)

# =======================
# مجلد مؤقت
# =======================
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# =======================
# رسالة الترحيب
# =======================
WELCOME_TEXT = (
    "👋 مرحبًا بك في بوت *جنكيز*\n\n"
    "هذا البوت مصمّم لدعم المستخدمين في المجالات التالية:\n"
    "• صُنّاع محتوى TikTok\n"
    "• لاعبي Free Fire\n"
    "• المهتمين بالبرمجة والتقنية\n\n"
    "🔹 يوفّر البوت أدوات آمنة وواقعية لمساعدتك في عملك.\n"
    "🔹 بدون أي محتوى مخالف أو عناوين مضللة.\n"
    "🔹 جميع الأدوات متوافقة مع سياسات TikTok الرسمية.\n\n"
    "مطور هذا البوت: جنكيز"
)

# =======================
# معلومات لغات البرمجة
# =======================
PROGRAMMING_INFO = (
    "💻 لغات البرمجة:\n\n"
    "• Python: سهلة وقوية للبوتات والتطبيقات.\n"
    "• JavaScript: أساس الويب والتفاعل.\n"
    "• HTML & CSS: بناء وتصميم المواقع.\n"
)

# =======================
# نصائح Free Fire طويلة
# =======================
FF_TIPS = (
    "🎮 نصائح مهمة لصنّاع محتوى Free Fire على TikTok:\n\n"
    "1️⃣ تجنّب العناوين المضللة مثل (شحن مجاني – هكر – متجر جواهر).\n"
    "2️⃣ لا تنشر محتوى يوهم المستخدمين بأي مزايا غير حقيقية.\n"
    "3️⃣ احترم حقوق النشر.\n"
    "4️⃣ المحتوى التعليمي أفضل.\n"
    "5️⃣ تجنب التكرار.\n"
    "6️⃣ استخدم موسيقى مرخصة من مكتبة TikTok.\n"
    "7️⃣ الجودة أهم من الكمية.\n"
    "8️⃣ لا تضع روابط خارجية مشبوهة.\n"
    "9️⃣ التزم بإرشادات المجتمع.\n"
    "🔟 كن صادقًا مع جمهورك."
)

# =======================
# لوحة التحكم
# =======================
def control_panel():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📥 تحميل TikTok", callback_data="download"),
        types.InlineKeyboardButton("💻 معلومات لغات البرمجة", callback_data="prog"),
        types.InlineKeyboardButton("🎮 نصائح Free Fire", callback_data="tips")
    )
    return kb

# =======================
# /start
# =======================
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(
        msg.chat.id,
        WELCOME_TEXT,
        reply_markup=control_panel(),
        parse_mode="Markdown"
    )

# =======================
# الأزرار
# =======================
# جلسة مؤقتة لتخزين جودة وقص الفيديو
user_sessions = {}

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    chat_id = call.message.chat.id
    user_sessions.setdefault(chat_id, {"quality": "720", "trim": None})

    if call.data == "download":
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(
            types.InlineKeyboardButton("360p", callback_data="q360"),
            types.InlineKeyboardButton("720p", callback_data="q720"),
            types.InlineKeyboardButton("1080p", callback_data="q1080")
        )
        bot.send_message(chat_id, "📌 اختر جودة الفيديو:", reply_markup=kb)
    elif call.data.startswith("q"):
        user_sessions[chat_id]["quality"] = call.data[1:]
        bot.send_message(chat_id, f"✅ تم اختيار الجودة: {call.data[1:]}p\nالآن يمكنك إرسال رابط الفيديو.")
    elif call.data == "prog":
        bot.send_message(chat_id, PROGRAMMING_INFO)
    elif call.data == "tips":
        bot.send_message(chat_id, FF_TIPS)

# =======================
# تحميل TikTok مع الجودة + ضغط + قص
# =======================
@bot.message_handler(func=lambda m: m.text and "tiktok.com" in m.text)
def download_tiktok(msg):
    chat_id = msg.chat.id
    url = msg.text.strip()

    # استرجاع إعدادات المستخدم
    session = user_sessions.get(chat_id, {"quality": "720", "trim": None})
    quality = session["quality"]

    bot.reply_to(msg, f"⏳ جاري تحميل الفيديو بجودة {quality}p...")

    video_id = str(uuid.uuid4())
    output_template = os.path.join(TEMP_DIR, f"{video_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": f"bestvideo[height<={quality}]+bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # ضغط تلقائي إذا أكبر من 50MB
        if os.path.getsize(filename) > 50 * 1024 * 1024:
            compressed_filename = filename.replace(".mp4", "_compressed.mp4")
            subprocess.run(f'ffmpeg -i "{filename}" -vcodec libx264 -crf 28 "{compressed_filename}" -y', shell=True)
            os.remove(filename)
            filename = compressed_filename

        # قص الفيديو إذا تم تحديد مدة (مثال: يمكن إضافة وظيفة لاحقًا)
        if session["trim"]:
            start, end = session["trim"]
            trimmed_filename = filename.replace(".mp4", "_trimmed.mp4")
            subprocess.run(f'ffmpeg -i "{filename}" -ss {start} -to {end} -c copy "{trimmed_filename}" -y', shell=True)
            os.remove(filename)
            filename = trimmed_filename

        with open(filename, "rb") as video:
            bot.send_video(chat_id, video, caption=f"✅ تم التحميل | جودة {quality}p | جنكيز")

        os.remove(filename)

    except Exception as e:
        bot.reply_to(msg, f"❌ فشل تحميل الفيديو.\n{e}\nتأكد أن الرابط عام وغير محذوف.")

# =======================
# رد افتراضي + إبقاء اللوحة ثابتة
# =======================
@bot.message_handler(func=lambda m: True)
def fallback(msg):
    bot.send_message(msg.chat.id, "ℹ️ استخدم لوحة التحكم بالأسفل 👇", reply_markup=control_panel())

# =======================
# تشغيل البوت
# =======================
print("🤖 Jankiz bot is running...")
bot.infinity_polling(skip_pending=True)