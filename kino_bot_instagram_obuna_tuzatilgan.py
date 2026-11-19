# ==================================================
# PROFESSIONAL TELEGRAM KINO BOT
# Python 3.10+
# ==================================================

# 2. IMPORTLAR

import os
import sqlite3
import logging
from dotenv import load_dotenv

load_dotenv()

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ==================================================
# 3. SOZLAMALAR
# ==================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YANGI_BOTFATHER_TOKENINI_BU_YERGA_QOYING")

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
except ValueError:
    raise ValueError(".env faylidagi ADMIN_ID faqat raqamlardan iborat bo'lishi kerak")

DB_NAME = os.getenv("DB_NAME", "kinolar.db")

if os.path.dirname(DB_NAME):
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)

INSTAGRAM_URL = "https://www.instagram.com/o79.ayub/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ==================================================
# 4. ADMIN TEKSHIRISH
# ==================================================

def is_admin(user_id):
    try:
        return int(user_id) == int(ADMIN_ID)
    except (ValueError, TypeError):
        return False

# ==================================================
# 5. DATABASE
# ==================================================

def create_database():
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                file_id TEXT NOT NULL
            )
        """)

    print("Database tayyor!")

def save_movie(title, description, file_id):
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            INSERT INTO movies (title, description, file_id)
            VALUES (?, ?, ?)
        """, (title, description, file_id))

def get_movies():
    with sqlite3.connect(DB_NAME) as db:
        return db.execute("""
            SELECT id, title FROM movies
            ORDER BY id DESC
        """).fetchall()

def get_movie(movie_id):
    with sqlite3.connect(DB_NAME) as db:
        return db.execute("""
            SELECT id, title, description, file_id
            FROM movies WHERE id = ?
        """, (movie_id,)).fetchone()

def delete_movie(movie_id):
    with sqlite3.connect(DB_NAME) as db:
        result = db.execute(
            "DELETE FROM movies WHERE id = ?",
            (movie_id,)
        )
        return result.rowcount > 0



def subscription_menu():
    keyboard = [
        [InlineKeyboardButton("📸 Instagramga obuna bo'lish", url=INSTAGRAM_URL)],
        [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="subscription_confirm")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_subscription_message(message):
    await message.reply_text(
        "🔒 Botdan foydalanish uchun Instagram sahifamizga obuna bo'ling.\n\n"
        "1. «Instagramga obuna bo'lish» tugmasini bosing.\n"
        "2. Instagramda @o79.ayub sahifasiga obuna bo'ling.\n"
        "3. Botga qaytib, «Obuna bo'ldim» tugmasini bosing.",
        reply_markup=subscription_menu()
    )

# ==================================================
# 6. MENYULAR
# ==================================================

def main_menu(user_id):
    # 1-tugma: Kino qidirish
    # 2-tugma: Yordam
    # Qolgan tugmalar saqlangan
    keyboard = [
        [
            InlineKeyboardButton(
                "🔎 Kino qidirish",
                callback_data="search"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ Yordam",
                callback_data="help"
            )
        ],
        [
            InlineKeyboardButton(
                "🎬 Barcha kinolar",
                callback_data="movies"
            )
        ],
        [
            InlineKeyboardButton(
                "🆕 Yangi kinolar",
                callback_data="new"
            )
        ]
    ]

    if is_admin(user_id):
        keyboard.append([
            InlineKeyboardButton(
                "👨‍💻 ADMIN PANEL",
                callback_data="admin_panel"
            )
        ])

    return InlineKeyboardMarkup(keyboard)


def admin_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Kino qo'shish",
                callback_data="add"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Kino o'chirish",
                callback_data="delete_menu"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Statistika",
                callback_data="stats"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="home"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)

# ==================================================
# 7. START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["instagram_confirmed"] = False
    await show_subscription_message(update.message)

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Sizning ID raqamingiz: {update.effective_user.id}"
    )

# ==================================================
# 8. ADMIN PANEL
# ==================================================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("instagram_confirmed", False):
        await show_subscription_message(update.message)
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    context.user_data.pop("state", None)

    await update.message.reply_text(
        "👨‍💻 ADMIN PANEL\n\nBo'limni tanlang:",
        reply_markup=admin_menu()
    )

# ==================================================
# 9. KINO RO'YXATI
# ==================================================

async def show_movies(message, page=0):
    movies = get_movies()

    if not movies:
        await message.reply_text("❌ Hozircha kinolar yo'q.")
        return

    start_index = page * 10
    selected = movies[start_index:start_index + 10]

    keyboard = []

    for movie_id, title in selected:
        keyboard.append([
            InlineKeyboardButton(
                f"🎬 {title}",
                callback_data=f"movie_{movie_id}"
            )
        ])

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Oldingi",
                callback_data=f"page_{page - 1}"
            )
        )

    if start_index + 10 < len(movies):
        navigation.append(
            InlineKeyboardButton(
                "Keyingi ➡️",
                callback_data=f"page_{page + 1}"
            )
        )

    if navigation:
        keyboard.append(navigation)

    await message.reply_text(
        "🎬 KINOLAR RO'YXATI:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================================================
# 10. KINO MA'LUMOTI
# ==================================================

async def show_movie(query, movie_id):
    movie = get_movie(movie_id)

    if not movie:
        await query.message.reply_text("❌ Kino topilmadi!")
        return

    _, title, description, file_id = movie

    keyboard = [[
        InlineKeyboardButton(
            "▶️ TOMOSHA QILISH",
            callback_data=f"watch_{movie_id}"
        )
    ]]

    await query.message.reply_text(
        f"🎬 Kino: {title}\n\n"
        f"📝 Ma'lumot: {description or 'Ma’lumot yo‘q'}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================================================
# 11. QIDIRUV
# ==================================================

async def search_movies(message, search_text):
    with sqlite3.connect(DB_NAME) as db:
        movies = db.execute("""
            SELECT id, title FROM movies
            WHERE title LIKE ?
            ORDER BY id DESC LIMIT 20
        """, (f"%{search_text}%",)).fetchall()

    if not movies:
        await message.reply_text("❌ Kino topilmadi!")
        return

    keyboard = []

    for movie_id, title in movies:
        keyboard.append([
            InlineKeyboardButton(
                f"🎬 {title}",
                callback_data=f"movie_{movie_id}"
            )
        ])

    await message.reply_text(
        "🔎 QIDIRUV NATIJALARI:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================================================
# 12. TUGMALAR
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "subscription_confirm":
        # Eslatma: Instagram obunasini Telegram bot API orqali tasdiqlab bo'lmaydi.
        context.user_data.clear()
        context.user_data["instagram_confirmed"] = True
        await query.message.reply_text(
            "✅ Davom etishingiz mumkin! Bot menyusi:",
            reply_markup=main_menu(user_id)
        )
        return

    if not context.user_data.get("instagram_confirmed", False):
        await show_subscription_message(query.message)
        return

    if data == "home":
        context.user_data.pop("state", None)
        await query.message.reply_text(
            "🏠 BOSH MENYU",
            reply_markup=main_menu(user_id)
        )

    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.answer(
                "⛔ Siz admin emassiz!",
                show_alert=True
            )
            return

        context.user_data.pop("state", None)

        await query.message.edit_text(
            "👨‍💻 ADMIN PANEL\n\nKerakli bo'limni tanlang:",
            reply_markup=admin_menu()
        )

    elif data == "movies" or data == "new":
        await show_movies(query.message)

    elif data == "search":
        context.user_data.clear()
        context.user_data["state"] = "search"

        await query.message.reply_text(
            "🔎 Kino nomini yozing:"
        )

    elif data == "help":
        await query.message.reply_text(
            "Salom! Kino nomini yozing yoki "
            "«Kino qidirish» tugmasini bosing."
        )

    elif data == "add":
        if not is_admin(user_id):
            await query.message.reply_text("⛔ Ruxsat yo'q!")
            return

        context.user_data.clear()
        context.user_data["state"] = "add_title"

        await query.message.reply_text(
            "➕ Kino nomini yuboring:"
        )

    elif data == "delete_menu":
        if not is_admin(user_id):
            await query.message.reply_text("⛔ Ruxsat yo'q!")
            return

        movies = get_movies()

        if not movies:
            await query.message.reply_text("Kinolar mavjud emas!")
            return

        keyboard = []

        for movie_id, title in movies:
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑 {title}",
                    callback_data=f"del_{movie_id}"
                )
            ])

        await query.message.reply_text(
            "O'chiriladigan kinoni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "stats":
        if not is_admin(user_id):
            await query.message.reply_text("⛔ Ruxsat yo'q!")
            return

        with sqlite3.connect(DB_NAME) as db:
            count = db.execute(
                "SELECT COUNT(*) FROM movies"
            ).fetchone()[0]

        await query.message.reply_text(
            f"📊 STATISTIKA\n\n🎬 Kinolar: {count} ta"
        )

    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        await show_movies(query.message, page)

    elif data.startswith("movie_"):
        movie_id = int(data.split("_")[1])
        await show_movie(query, movie_id)

    elif data.startswith("watch_"):
        movie_id = int(data.split("_")[1])
        movie = get_movie(movie_id)

        if not movie:
            await query.message.reply_text("Kino topilmadi!")
            return

        await query.message.reply_video(
            video=movie[3],
            caption=f"🎬 {movie[1]}"
        )

    elif data.startswith("del_"):
        if not is_admin(user_id):
            await query.message.reply_text("⛔ Ruxsat yo'q!")
            return

        movie_id = int(data.split("_")[1])

        if delete_movie(movie_id):
            await query.message.reply_text("✅ Kino o'chirildi!")
        else:
            await query.message.reply_text("Kino topilmadi!")

# ==================================================
# 13. MATN QABUL QILISH
# ==================================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("instagram_confirmed", False):
        await show_subscription_message(update.message)
        return

    state = context.user_data.get("state")
    text = update.message.text
    user_id = update.effective_user.id

    if state and state.startswith("add_") and not is_admin(user_id):
        context.user_data.clear()
        await update.message.reply_text("⛔ Ruxsat yo'q!")
        return

    if state == "search":
        context.user_data.pop("state", None)
        await search_movies(update.message, text)

    elif state == "add_title":
        context.user_data["title"] = text
        context.user_data["state"] = "add_description"

        await update.message.reply_text(
            "📝 Kino haqida ma'lumot yozing:"
        )

    elif state == "add_description":
        context.user_data["description"] = text
        context.user_data["state"] = "add_video"

        await update.message.reply_text(
            "🎥 Endi kino videosini yuboring:"
        )

    elif state == "add_video":
        await update.message.reply_text(
            "❗ Iltimos, video fayl yuboring!"
        )

    else:
        await update.message.reply_text(
            "Menyudan foydalaning:",
            reply_markup=main_menu(user_id)
        )

# ==================================================
# 14. VIDEO QABUL QILISH
# ==================================================

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("instagram_confirmed", False):
        await show_subscription_message(update.message)
        return

    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    if context.user_data.get("state") != "add_video":
        await update.message.reply_text(
            "Avval admin paneldan kino qo'shishni boshlang!"
        )
        return

    video = update.message.video

    if not video:
        await update.message.reply_text("Video topilmadi!")
        return

    title = context.user_data["title"]
    description = context.user_data["description"]

    save_movie(title, description, video.file_id)

    context.user_data.clear()
    context.user_data["instagram_confirmed"] = True

    await update.message.reply_text(
        "✅ KINO MUVAFFAQIYATLI SAQLANDI!\n\n"
        f"🎬 Nomi: {title}",
        reply_markup=admin_menu()
    )

# ==================================================
# 15. XATOLARNI USHLASH
# ==================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(
        "Xatolik yuz berdi:",
        exc_info=context.error
    )

# ==================================================
# 16. BOTNI ISHGA TUSHIRISH
# ==================================================

def main():

    if (
        not TOKEN
        or TOKEN == "YANGI_BOTFATHER_TOKENINI_BU_YERGA_QOYING"
        or TOKEN == "SIZNING_BOT_TOKENINGIZ"
        or ":" not in TOKEN
    ):
        raise ValueError(
            "Haqiqiy TELEGRAM_BOT_TOKEN qiymatini kiriting. "
            "BotFather tokeni odatda '123456789:ABC...' ko'rinishida bo'ladi."
        )

    if ADMIN_ID == 123456789:
        raise ValueError(
            "ADMIN_ID ni o'zingizning Telegram ID raqamingizga almashtiring!"
        )

    create_database()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CommandHandler("admin", admin_command))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(
        MessageHandler(filters.VIDEO, video_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    app.add_error_handler(error_handler)

    print("=" * 45)
    print("KINO BOT ISHGA TUSHDI!")
    print(f"ADMIN ID: {ADMIN_ID}")
    print("=" * 45)

    app.run_polling()


if __name__ == "__main__":
    main()
