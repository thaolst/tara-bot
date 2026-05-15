import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from .config import config
from .agents import Agent

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger("tara-bot")

sessions: dict[int, Agent] = {}

def get_agent(user_id: int) -> Agent:
    if user_id not in sessions:
        sessions[user_id] = Agent()
    return sessions[user_id]

def is_allowed(user_id: int) -> bool:
    allowed = config.allowed_user_id
    if not allowed:
        return True
    return str(user_id) in allowed.split(",")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    uid = update.effective_user.id
    if not is_allowed(uid):
        await update.message.reply_text("Xin lỗi, bạn không có quyền sử dụng bot này.")
        return

    agent = get_agent(uid)
    try:
        response = await agent.chat(update.message.text)
        await update.message.reply_text(response)
    except Exception as e:
        log.error(f"Error: {e}")
        await update.message.reply_text(f"😵 Có lỗi xảy ra. Vui lòng kiểm tra lại API Key trên Render.")

if __name__ == '__main__':
    if not config.telegram_token:
        log.error("TELEGRAM_TOKEN is not set!")
    else:
        app = ApplicationBuilder().token(config.telegram_token).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        log.info("Bot is running...")
        app.run_polling()
