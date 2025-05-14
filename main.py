import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# 🟩 مرحله 1: ساخت فایل کوکی معتبر (Netscape Format)
cookie_text = """# Netscape HTTP Cookie File
.instagram.com\tTRUE\t/\tTRUE\t9999999999\tds_user_id\t63966829241
.instagram.com\tTRUE\t/\tTRUE\t9999999999\tsessionid\t63966829241%3A1jphytJbfG5RJD%3A12%3AAYdKr-jtNFjL1YlBJkXWgdZBxxZt_MOh7heLrB9KbQ
"""

with open("instagram_cookies.txt", "w", encoding="utf-8") as f:
    f.write(cookie_text)

# 🟩 مرحله 2: دریافت توکن ربات
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN در متغیرهای محیطی تعریف نشده.")

bot = telebot.TeleBot(TOKEN)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_links = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 سلام! لینک پست، استوری یا هایلایت اینستاگرام رو بفرست. اگر خصوصی هم باشه مشکلی نیست 😉"
    )

@bot.message_handler(func=lambda m: 'instagram.com' in m.text)
def handle_link(message):
    user_links[message.chat.id] = message.text

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📥 دانلود محتوا", callback_data="download"))
    bot.send_message(message.chat.id, "✅ لینک دریافت شد. برای ادامه روی دکمه زیر بزن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "download")
def download_content(call):
    chat_id = call.message.chat.id
    url = user_links.get(chat_id)
    bot.send_message(chat_id, "⏳ در حال پردازش و دانلود از اینستاگرام...")

    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'cookiefile': 'instagram_cookies.txt'
        }

        downloaded_files = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if 'entries' in info:
                for entry in info['entries']:
                    path = ydl.prepare_filename(entry)
                    ext = entry.get('ext', 'mp4')
                    downloaded_files.append((path, ext))
            else:
                path = ydl.prepare_filename(info)
                ext = info.get('ext', 'mp4')
                downloaded_files.append((path, ext))

        for file_path, ext in downloaded_files:
            with open(file_path, 'rb') as f:
                if ext in ['jpg', 'jpeg', 'png']:
                    bot.send_photo(chat_id, f)
                elif ext == 'mp4':
                    bot.send_video(chat_id, f)
                else:
                    bot.send_document(chat_id, f)
            os.remove(file_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا در دانلود:\n{e}")

# 🟩 اجرای دائمی ربات
bot.infinity_polling()
