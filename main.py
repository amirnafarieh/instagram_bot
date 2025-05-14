import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import subprocess

# 📌 کوکی اینستاگرام
cookie_text = """# Netscape HTTP Cookie File
.instagram.com\tTRUE\t/\tTRUE\t9999999999\tds_user_id\t63966829241
.instagram.com\tTRUE\t/\tTRUE\t9999999999\tsessionid\t63966829241%3A1jphytJbfG5RJD%3A12%3AAYdKr-jtNFjL1YlBJkXWgdZBxxZt_MOh7heLrB9KbQ
"""
with open("instagram_cookies.txt", "w", encoding="utf-8") as f:
    f.write(cookie_text)

# 🔐 توکن
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN not set.")
bot = telebot.TeleBot(TOKEN)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_links = {}
user_media_info = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "👋 لینک اینستاگرام رو بفرست (پست، استوری، ریلز یا هایلایت)")

@bot.message_handler(func=lambda m: 'instagram.com' in m.text)
def handle_link(message):
    chat_id = message.chat.id
    url = message.text
    user_links[chat_id] = url

    bot.send_message(chat_id, "🔍 در حال بررسی لینک...")

    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': False,
            'cookiefile': 'instagram_cookies.txt'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        user_media_info[chat_id] = info

        markup = InlineKeyboardMarkup(row_width=2)
        buttons = []

        if 'entries' in info:
            has_video = any(e.get('ext') == 'mp4' for e in info['entries'])
            has_image = any(e.get('ext') in ['jpg', 'jpeg', 'png'] for e in info['entries'])

            if has_image:
                buttons.append(InlineKeyboardButton("🖼️ دانلود همه عکس‌ها", callback_data="album_photos"))
            if has_video:
                buttons.append(InlineKeyboardButton("🎞️ دانلود همه ویدیوها", callback_data="album_videos"))
                buttons.append(InlineKeyboardButton("🎧 دانلود همه موزیک‌ها", callback_data="album_audios"))
        else:
            ext = info.get('ext', '')
            if ext in ['jpg', 'jpeg', 'png']:
                buttons.append(InlineKeyboardButton("📷 دانلود عکس", callback_data="photo"))
            elif ext == 'mp4':
                buttons.append(InlineKeyboardButton("🎥 دانلود ویدیو", callback_data="video"))
                buttons.append(InlineKeyboardButton("🎧 دانلود موزیک", callback_data="audio"))

        for btn in buttons:
            markup.add(btn)

        bot.send_message(chat_id, "👇 لطفاً انتخاب کن:", reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا:\n{e}")

def download_and_send(chat_id, info, mode):
    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'quiet': True,
            'cookiefile': 'instagram_cookies.txt'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            entries = info['entries'] if 'entries' in info else [info]
            for entry in entries:
                path = ydl.prepare_filename(entry)
                if not os.path.exists(path):
                    ydl.download([entry['webpage_url']])

                ext = path.split('.')[-1]

                if mode in ['photo', 'album_photos'] and ext in ['jpg', 'jpeg', 'png']:
                    with open(path, 'rb') as f:
                        bot.send_photo(chat_id, f)
                    os.remove(path)

                elif mode in ['video', 'album_videos'] and ext == 'mp4':
                    with open(path, 'rb') as f:
                        bot.send_video(chat_id, f)
                    os.remove(path)

                elif mode in ['audio', 'album_audios'] and ext == 'mp4':
                    mp3_path = path.rsplit('.', 1)[0] + '.mp3'
                    subprocess.run([
                        'ffmpeg', '-i', path,
                        '-vn', '-ab', '192k',
                        '-ar', '44100',
                        '-y', mp3_path
                    ])
                    with open(mp3_path, 'rb') as f:
                        bot.send_audio(chat_id, f)
                    os.remove(mp3_path)
                    os.remove(path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا در دانلود یا تبدیل:\n{e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    info = user_media_info.get(chat_id)
    if not info:
        bot.send_message(chat_id, "❌ اطلاعات پیدا نشد. لطفاً لینک رو دوباره ارسال کن.")
        return

    download_and_send(chat_id, info, call.data)

bot.infinity_polling()
