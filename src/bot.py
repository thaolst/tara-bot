#!/usr/bin/env python3
"""Tara Bot — Telegram bot entry point."""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import Config
from .agents import Agent

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("tara-bot")


# ── In-memory sessions ───────────────────────────────────────────────

sessions: dict[int, Agent] = {}
locks: dict[int, asyncio.Lock] = {}


def get_agent(user_id: int) -> Agent:
    """Get or create an agent session for a user."""
    if user_id not in sessions:
        sessions[user_id] = Agent()
    return sessions[user_id]


def get_lock(user_id: int) -> asyncio.Lock:
    """Per-user lock: 2 message cua cung 1 user phai xu ly tuan tu de khong hong history."""
    if user_id not in locks:
        locks[user_id] = asyncio.Lock()
    return locks[user_id]


# ── Authorization ────────────────────────────────────────────────────

def is_allowed(user_id: int) -> bool:
    allowed = Config.allowed_user_id
    if not allowed:
        return True  # no restriction set
    return str(user_id) in allowed.split(",")


def authorize(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else 0
    if not is_allowed(uid):
        log.warning(f"Blocked unauthorized access: {uid}")
        return False
    return True


# ── Handlers ─────────────────────────────────────────────────────────

async def start(update: Update, _context) -> None:
    if not authorize(update):
        await update.message.reply_text(
            "⛔ Bạn không phải chủ bot này."
        )
        return

    await update.message.reply_text(
        "👋 *Tara Bot — Săn giá, tìm deal*\n\n"
        "Mình có thể:\n"
        "✈️ Tìm vé máy bay: *\"vé SG Đà Nẵng cuối tuần\"*\n"
        "🛒 So sánh giá: *\"iPhone 16 giá bao nhiêu\"*\n\n"
        "Thử đi ạ!",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, _context) -> None:
    if not authorize(update):
        return

    uid = update.effective_user.id
    text = update.message.text.strip()

    if not text:
        return

    log.info(f"[{uid}] {text}")

    # Show typing while thinking
    await update.message.chat.send_action("typing")

    try:
        agent = get_agent(uid)

        # agent.chat la sync (tool-use loop, co the chay vai chuc giay).
        # Goi truc tiep se block event loop -> bot dung hinh voi moi user khac.
        # asyncio.to_thread day no sang thread pool, event loop van phuc vu
        # user khac. Lock per-user giu thu tu message cua cung 1 user.
        async with get_lock(uid):
            reply = await asyncio.to_thread(agent.chat, text)

        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        log.exception("Error processing message")
        await update.message.reply_text(
            f"😵 Có lỗi xảy ra: {e}\nThử lại sau nhé!"
        )


async def reset(update: Update, _context) -> None:
    """Reset conversation history."""
    if not authorize(update):
        return
    uid = update.effective_user.id
    if uid in sessions:
        del sessions[uid]
    await update.message.reply_text("🔄 Đã reset conversation.")


async def uptime(update: Update, _context) -> None:
    """Show a simple health check — useful for monitoring."""
    if not authorize(update):
        return
    await update.message.reply_text(
        f"✅ Tara Bot đang chạy | "
        f"{len(sessions)} active session(s)"
    )


# ── Health check HTTP server (for Fly.io) ─────────────────────────────

class HealthHandler(BaseHTTPRequestHandler):
    """Minimal health endpoint so Fly.io doesn't kill the machine."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, fmt, *args) -> None:
        pass  # silence log spam


def run_health_server() -> None:
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    log.info("Health server listening on :8080")
    server.serve_forever()


# ── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    token = Config.telegram_token
    if not token:
        raise SystemExit("TELEGRAM_TOKEN not set")

    # Start health server in background thread for Fly.io
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("uptime", uptime))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    log.info("🚀 Tara Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
