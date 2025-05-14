import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import subprocess

# 🔐 فایل کوکی اینستاگرام
cookie_text = """# Netscape HTTP Cookie File
.instagram.com\tTRUE\t/\tTRUE\t9999999999\tds_user_id\t63966829241
.instagram.com\tTRUE\t/\tTRUE\t9999999999\tsessionid\t63966829241%3A1jphytJbfG5RJD%3A12%3AAYdKr-jtNFjL1YlBJkXWgdZBxxZt_MOh7heLrB9KbQ
"""
with open("instagram_cookies.txt", "w", encoding="utf-8") as f:
    f.write(cookie_text)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set.")

bot = telebot.TeleBot(TOKEN)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_links = {}
user_media_info = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "👋 سلام! لینک پست، استوری یا هایلایت اینستاگرام رو بفرست.")

@bot.message_handler(func=lambda m: 'instagram.com' in m.text)
def handle_link(message):
    chat_id = message.chat.id
    url = message.text
    user_links[chat_id] = url

    bot.send_message(chat_id, "⏳ در حال بررسی لینک...")

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

        # چند آیتمی (آلبوم)
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

        bot.send_message(chat_id, "👇 یکی از گزینه‌ها رو انتخاب کن:", reply_markup=markup)

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
            if 'entries' in info:
                entries = info['entries']
            else:
                entries = [info]

            for entry in entries:
                ext = entry.get('ext', 'mp4')
                is_video = ext == 'mp4'
                is_image = ext in ['jpg', 'jpeg', 'png']
                path = ydl.prepare_filename(entry)

                if not os.path.exists(path):
                    ydl.download([entry['webpage_url']])

                if mode == 'photo' and is_image:
                    with open(path, 'rb') as f:
                        bot.send_photo(chat_id, f)
                    os.remove(path)

                elif mode == 'video' and is_video:
                    with open(path, 'rb') as f:
                        bot.send_video(chat_id, f)
                    os.remove(path)

                elif mode == 'audio' and is_video:
                    mp3_path = path.rsplit('.', 1)[0] + '.mp3'
                    subprocess.run([
                        'ffmpeg', '-i', path,
                        '-vn', '-ab', '192k',
                        '-ar', '44100',
                        '-y', mp3_path
                    ])
                    with open(mp3_path, 'rb') as f:
                        bot.send_audio(chat_id, f)
                    os.remove(path)
                    os.remove(mp3_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا در دانلود:\n{e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    info = user_media_info.get(chat_id)
    if not info:
        bot.send_message(chat_id, "❌ اطلاعات فایل یافت نشد. لطفاً لینک رو دوباره بفرست.")
        return

    data = call.data
    if data == "photo":
        download_and_send(chat_id, info, 'photo')
    elif data == "video":
        download_and_send(chat_id, info, 'video')
    elif data == "audio":
        download_and_send(chat_id, info, 'audio')
    elif data == "album_photos":
        download_and_send(chat_id, info, 'photo')
    elif data == "album_videos":
        download_and_send(chat_id, info, 'video')
    elif data == "album_audios":
        download_and_send(chat_id, info, 'audio')

bot.infinity_polling()
