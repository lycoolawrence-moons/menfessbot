import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")   # contoh: -100xxxxxxxxxx
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # id telegram kamu
DELAY = int(os.getenv("DELAY", 60))

user_cooldown = {}
menfess_counter = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kirim pesan untuk mengirim menfess.\nPesan akan direview admin dulu."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global menfess_counter

    user_id = update.message.from_user.id
    text = update.message.text

    # Anti spam cooldown
    if user_id in user_cooldown:
        await update.message.reply_text(
            f"Tunggu {DELAY} detik sebelum kirim lagi."
        )
        return

    user_cooldown[user_id] = True
    asyncio.create_task(remove_cooldown(user_id))

    # Kirim ke admin untuk approval
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve|{user_id}|{menfess_counter}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject|{user_id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Menfess #{menfess_counter}\n\n{text}",
        reply_markup=keyboard
    )

    await update.message.reply_text("Menfess dikirim ke admin untuk direview.")

    context.bot_data[str(menfess_counter)] = text
    menfess_counter += 1


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    action = data[0]
    user_id = int(data[1])

    if action == "approve":
        number = data[2]
        text = context.bot_data.get(number)

        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"💌 MENFESS #{number}\n\n{text}\n\n— Anonymous"
        )

        await context.bot.send_message(
            chat_id=user_id,
            text="Menfess kamu sudah diposting!"
        )

        await query.edit_message_text("Menfess disetujui & diposting.")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text="Maaf, menfess kamu ditolak admin."
        )
        await query.edit_message_text("Menfess ditolak.")


async def remove_cooldown(user_id):
    await asyncio.sleep(DELAY)
    user_cooldown.pop(user_id, None)


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())