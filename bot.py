import os
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

load_dotenv()

TOKEN = os.environ["TEL_BOT_TOKEN"]
ALLOWED_CHAT_ID = int(os.environ["ALLOWED_CHAT_ID"])
INBOX_PATH = Path(os.environ["INBOX_PATH"])
INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)

YT_REGEX = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/shorts/|youtube\.com/watch\?v=|youtu\.be/)([\w-]+)"
)


def is_authorized(update: Update) -> bool:
    return update.effective_chat.id == ALLOWED_CHAT_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "YT inbox bot ready. Forward shorts here. /list to see queue. /clear to wipe."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized.")
        return

    text = update.message.text or ""
    matches = YT_REGEX.findall(text)

    if not matches:
        await update.message.reply_text("No YouTube URL found.")
        return

    timestamp = datetime.utcnow().isoformat()
    lines = []
    for video_id in matches:
        url = f"https://youtube.com/watch?v={video_id}"
        lines.append(f"{timestamp}\t{url}\n")

    with INBOX_PATH.open("a", encoding="utf-8") as f:
        f.writelines(lines)

    await update.message.reply_text(f"Queued {len(matches)} video(s).")


async def list_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    if not INBOX_PATH.exists():
        await update.message.reply_text("Queue empty.")
        return

    lines = INBOX_PATH.read_text(encoding="utf-8").strip().splitlines()
    count = len(lines)
    preview = "\n".join(lines[-5:]) if lines else "(empty)"
    await update.message.reply_text(f"Queue: {count} item(s)\n\nLast 5:\n{preview}")


async def clear_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    if INBOX_PATH.exists():
        INBOX_PATH.unlink()
    await update.message.reply_text("Queue cleared.")


def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_queue))
    app.add_handler(CommandHandler("clear", clear_queue))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
