import os
import yt_dlp
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8518071875:AAEHyIbJp2Qc3UFlD0dfXjlv2R6azoLRFqE"

DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

user_busy = {}

def progress_hook(d, context):

    if d['status'] == 'downloading':

        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)

        if total:
            percent = int(downloaded / total * 100)

            msg = context['msg']
            last = context.get('last', -1)

            if percent != last and percent % 5 == 0:
                try:
                    msg.edit_text(f"⏳ جاري التحميل {percent}%")
                except:
                    pass

                context['last'] = percent


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 اهلا بيك\n\n"
        "ابعت لينك فيديو من:\n"
        "TikTok - Instagram - YouTube - Facebook\n\n"
        "وهتختار تحميل الفيديو او الصوت."
    )


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    if user_busy.get(user):

        await update.message.reply_text("⏳ استنى التحميل الحالي يخلص.")
        return

    context.user_data["url"] = update.message.text

    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو", callback_data="video"),
            InlineKeyboardButton("🎧 صوت", callback_data="audio")
        ]
    ]

    await update.message.reply_text(
        "اختار نوع التحميل:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user.id
    user_busy[user] = True

    url = context.user_data.get("url")

    msg = await query.edit_message_text("⏳ بدء التحميل...")

    progress_data = {
        "msg": msg,
        "last": -1
    }

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(id)s.%(ext)s',
        'noplaylist': True,
        'progress_hooks': [lambda d: progress_hook(d, progress_data)]
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        if query.data == "video":

            await msg.edit_text("📤 جاري ارسال الفيديو...")

            await query.message.reply_video(video=open(file_path, 'rb'))

        else:

            await msg.edit_text("🎧 استخراج الصوت...")

            audio_path = file_path.rsplit(".", 1)[0] + ".mp3"

            os.system(f'ffmpeg -i "{file_path}" -q:a 0 -map a "{audio_path}"')

            await query.message.reply_audio(audio=open(audio_path, 'rb'))

            os.remove(audio_path)

        os.remove(file_path)

        await msg.delete()

    except Exception as e:

        await msg.edit_text("❌ حصل خطأ أثناء التحميل")

    user_busy[user] = False


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), receive_link))
app.add_handler(CallbackQueryHandler(download))

app.run_polling()