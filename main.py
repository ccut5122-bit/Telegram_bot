import os
import yt_dlp
from telegram import Update, BotCommand, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# 🔑 Token from environment
TOKEN = os.getenv("KEY")

users = set()
mode = {}

# Menu
main_menu = [
    ["YouTube Downloader"],
    ["Help"]
]

download_menu = [
    ["Video", "Audio"],
    ["Back"]
]

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    users.add(user)

    await update.message.reply_text(
        "🚀 Bot Ready!",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# ---------------- HELP ----------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send YouTube link after selecting Video/Audio")

# ---------------- MENU ----------------
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user.id

    # Main menu
    if text == "YouTube Downloader":
        mode[user] = "yt"
        await update.message.reply_text(
            "Select format:",
            reply_markup=ReplyKeyboardMarkup(download_menu, resize_keyboard=True)
        )
        return

    if text == "Help":
        await help_cmd(update, context)
        return

    if text == "Back":
        await update.message.reply_text(
            "Main Menu",
            reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        )
        return

    if text in ["Video", "Audio"]:
        if user not in mode:
            mode[user] = "yt"

        mode[user] = mode[user] + ("_audio" if text == "Audio" else "_video")
        await update.message.reply_text("Send YouTube link now")
        return

    # Download logic
    if "http" in text:
        await update.message.reply_text("Downloading... ⏳")

        try:
            is_audio = "audio" in mode.get(user, "")

            ydl_opts = {
                "format": "bestaudio/best" if is_audio else "best",
                "outtmpl": f"{user}_%(id)s.%(ext)s",
                "noplaylist": True,
            }

            if is_audio:
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = f"{user}_{info['id']}.{'mp3' if is_audio else 'mp4'}"

            if os.path.exists(filename):
                with open(filename, "rb") as f:
                    if is_audio:
                        await update.message.reply_audio(f)
                    else:
                        await update.message.reply_video(f)

                os.remove(filename)
                await update.message.reply_text("✅ Done!")
            else:
                await update.message.reply_text("❌ File not found")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

# ---------------- MAIN ----------------
async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Start"),
        BotCommand("help", "Help")
    ])

app = Application.builder().token(TOKEN).post_init(set_commands).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

print("Bot Running...")
app.run_polling()
