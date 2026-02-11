#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
from telebot import TeleBot, types
import yt_dlp
from dotenv import load_dotenv
import subprocess
from flask import Flask
from threading import Thread

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
    "• المهتمين بالبرمجة والتقنية\n\n"
    "🔹 يوفّر البوت أدوات آمنة وواقعية لمساعدتك في عملك.\n"
    "🔹 بدون أي محتوى مخالف أو عناوين مضللة.\n"
    "🔹 جميع الأدوات متوافقة مع سياسات TikTok الرسمية.\n\n"
    "⚡ البوت لا زال تحت التطوير والمميزات الأفضل والأفضل قادمة قريبًا!\n\n"
    "مطور هذا البوت: جنكيز"
)

# =======================
# معلومات لغات البرمجة
# =======================
PROGRAMMING_INFO = (
    "💻 لغات البرمجة:\n\n"
    "• Python: قوية وسهلة للبوتات والتطبيقات.\n"
    "• JavaScript: أساسي للويب والتفاعل.\n"
    "• HTML & CSS: لبناء وتصميم المواقع.\n"
)

# =======================
# نصائح لصناع محتوى TikTok
# =======================
TIKTOK_TIPS = (
    "🎯 نصائح مهمة لصنّاع محتوى TikTok:\n\n"
    "1️⃣ تجنّب نشر محتوى مضلل أو محمي بحقوق الآخرين.\n"
    "2️⃣ لا تستخدم عناوين خادعة مثل: شحن مجاني، هكر، متجر جواهر.\n"
    "3️⃣ التزم بالموسيقى والصوتيات المرخصة في TikTok.\n"
    "4️⃣ قم بعمل محتوى أصلي وتفاعلي ليظهر في الاكسبلور.\n"
    "5️⃣ التكرار المفرط يقلل الوصول والمشاهدات.\n"
    "6️⃣ احرص على جودة الفيديو والصوت أكثر من الكمية.\n"
    "7️⃣ استخدم هاشتاغات دقيقة وشائعة لتعزيز الوصول.\n"
    "8️⃣ التفاعل مع التعليقات والمشاهدين يزيد من انتشار المحتوى.\n"
    "9️⃣ لا تنشر روابط خارجية أو صفحات مشبوهة.\n"
    "🔟 اتبع سياسات المجتمع لتجنب حظر الحساب أو تخفيض الرؤية.\n"
)

# =======================
# لوحة التحكم
# =======================
def control_panel():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📥 تحميل TikTok بدون علامة مائية", callback_data="download"),
        types.InlineKeyboardButton("💻 معلومات لغات البرمجة", callback_data="prog"),
        types.InlineKeyboardButton("🎯 نصائح لصناع محتوى TikTok", callback_data="tips")
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
user_sessions = {}

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    chat_id = call.message.chat.id
    user_sessions.setdefault(chat_id, {"quality": "720"})

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
        bot.send_message(chat_id, TIKTOK_TIPS)

# =======================
# تحميل TikTok بدون علامة مائية
# =======================
@bot.message_handler(func=lambda m: m.text and "tiktok.com" in m.text)
def download_tiktok(msg):
    chat_id = msg.chat.id
    url = msg.text.strip()

    session = user_sessions.get(chat_id, {"quality": "720"})
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
# Keep Alive 24/7 مع Flask
# =======================
app = Flask("")

@app.route("/")
def home():
    return "Jankiz bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

t = Thread(target=run)
t.start()

# =======================
# تشغيل البوت
# =======================
print("🤖 Jankiz bot is running...")
bot.infinity_polling(skip_pending=True)
