import os
import telebot
import yt_dlp

# گرفتن توکن از محیط Railway
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "سلام! 👋\nلینک پست اینستاگرام رو بفرست تا دانلودش کنم و برات بفرستم.")

@bot.message_handler(func=lambda m: 'instagram.com' in m.text)
def download_instagram_post(message):
    url = message.text
    bot.send_message(message.chat.id, "🔄 در حال دانلود فایل از اینستاگرام...")

    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'quiet': True,
            'format': 'best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        with open(file_path, 'rb') as f:
            if file_path.endswith('.mp4'):
                bot.send_video(message.chat.id, f)
            else:
                bot.send_document(message.chat.id, f)

        os.remove(file_path)  # پاک کردن فایل پس از ارسال

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطایی رخ داد:\n{e}")

bot.infinity_polling()
