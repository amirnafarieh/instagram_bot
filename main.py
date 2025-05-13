import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

user_links = {}  # ذخیره لینک ارسالی کاربران
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 سلام! خوش اومدی به ربات دانلود از اینستاگرام.\n\n📥 لطفاً لینک پست اینستاگرام رو بفرست تا بتونی ویدئو یا صداشو دریافت کنی."
    )

@bot.message_handler(func=lambda m: 'instagram.com' in m.text)
def handle_instagram_link(message):
    user_links[message.chat.id] = message.text

    # کلیدهای شیشه‌ای برای انتخاب نوع فایل
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎥 ویدیو (MP4)", callback_data="video"),
        InlineKeyboardButton("🎧 صدا (MP3)", callback_data="audio")
    )
    bot.send_message(
        message.chat.id,
        "✅ لینک دریافت شد! حالا انتخاب کن که می‌خوای ویدیو بگیری یا فقط صدا:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ['video', 'audio'])
def process_format_selection(call):
    chat_id = call.message.chat.id
    choice = call.data
    url = user_links.get(chat_id)

    if not url:
        bot.send_message(chat_id, "❌ لینک پیدا نشد. لطفاً دوباره لینک اینستاگرام رو بفرست.")
        return

    bot.send_message(chat_id, "⏳ در حال پردازش و دانلود فایل، لطفاً صبر کن...")

    try:
        # تنظیمات yt-dlp برای ویدیو یا صدا
        outtmpl = f'{DOWNLOAD_DIR}/%(title)s.%(ext)s'
        ydl_opts = {
            'outtmpl': outtmpl,
            'quiet': True,
            'format': 'bestaudio/best' if choice == 'audio' else 'bestvideo+bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if choice == 'audio' else []
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            if choice == 'audio':
                filepath = filepath.rsplit('.', 1)[0] + '.mp3'

        # ارسال فایل به کاربر
        with open(filepath, 'rb') as f:
            if choice == 'audio':
                bot.send_audio(chat_id, f)
            else:
                bot.send_video(chat_id, f)

        os.remove(filepath)

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا در پردازش فایل: {str(e)}")
