import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from content import BODY_PARTS, CATEGORY_LABELS

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def keyboard_main_menu():
    buttons = []
    row = []
    for key, part in BODY_PARTS.items():
        row.append(InlineKeyboardButton(f"{part['emoji']} {part['name']}", callback_data=f"bp:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def keyboard_categories(part_key):
    part = BODY_PARTS[part_key]
    buttons = []
    for cat_key, cat_label in CATEGORY_LABELS.items():
        if part.get(cat_key):
            buttons.append([InlineKeyboardButton(cat_label, callback_data=f"cat:{part_key}:{cat_key}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back:main")])
    return InlineKeyboardMarkup(buttons)

def keyboard_items(part_key, cat_key):
    items = BODY_PARTS[part_key].get(cat_key, [])
    buttons = []
    for i, item in enumerate(items):
        buttons.append([InlineKeyboardButton(item["title"], callback_data=f"vid:{part_key}:{cat_key}:{i}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data=f"bp:{part_key}")])
    return InlineKeyboardMarkup(buttons)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я помогу найти упражнения и методы самопомощи для любой части тела.\n\n👇 Выбери, что болит или беспокоит:",
        reply_markup=keyboard_main_menu(),
    )

async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👇 Выбери часть тела:", reply_markup=keyboard_main_menu())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back:main":
        await query.edit_message_text("👇 Выбери часть тела:", reply_markup=keyboard_main_menu())
        return

    if data.startswith("bp:"):
        part_key = data[3:]
        if part_key not in BODY_PARTS:
            return
        part = BODY_PARTS[part_key]
        await query.edit_message_text(
            f"{part['emoji']} *{part['name']}*\n\nЧто тебя интересует?",
            parse_mode="Markdown",
            reply_markup=keyboard_categories(part_key),
        )
        return

    if data.startswith("cat:"):
        _, part_key, cat_key = data.split(":")
        if part_key not in BODY_PARTS:
            return
        part = BODY_PARTS[part_key]
        cat_label = CATEGORY_LABELS.get(cat_key, "")
        await query.edit_message_text(
            f"{part['emoji']} *{part['name']}* - {cat_label}\n\nВыбери упражнение или технику:",
            parse_mode="Markdown",
            reply_markup=keyboard_items(part_key, cat_key),
        )
        return

    if data.startswith("vid:"):
        _, part_key, cat_key, idx_str = data.split(":")
        idx = int(idx_str)
        if part_key not in BODY_PARTS:
            return
        items = BODY_PARTS[part_key].get(cat_key, [])
        if idx >= len(items):
            return
        item = items[idx]
        await query.edit_message_text(
            f"*{item['title']}*\n\n_{item['desc']}_\n\nОткрой видео по кнопке ниже:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Смотреть видео", url=item["video"])],
                [InlineKeyboardButton("📋 К списку", callback_data=f"cat:{part_key}:{cat_key}")],
                [InlineKeyboardButton("🔙 Выбрать часть тела", callback_data="back:main")],
            ]),
        )
        return

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CallbackQueryHandler(on_callback))
    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
