import sqlite3
import logging
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)


DB_FILE = "farm.db"

OWNER_ID = 844645311

def init_broadcast_db():
    """Инициализация таблиц для рассылок и опросов"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    

    c.execute("""CREATE TABLE IF NOT EXISTS broadcast_users (
                 user_id INTEGER PRIMARY KEY
              )""")
    

    c.execute("""CREATE TABLE IF NOT EXISTS polls (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 message TEXT NOT NULL,
                 yes_count INTEGER DEFAULT 0,
                 no_count INTEGER DEFAULT 0,
                 created_at TEXT
              )""")
    

    c.execute("""CREATE TABLE IF NOT EXISTS poll_votes (
                 poll_id INTEGER,
                 user_id INTEGER,
                 vote TEXT,
                 PRIMARY KEY (poll_id, user_id)
              )""")
    
    conn.commit()
    conn.close()
    print("[BROADCAST] База для рассылок и опросов готова")

init_broadcast_db()


def register_user_for_broadcast(user_id: int):
    """Добавляем пользователя в базу для рассылок"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO broadcast_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📊 Создать опрос", callback_data="admin_create_poll"),
        InlineKeyboardButton("📈 Статистика последнего опроса", callback_data="admin_poll_stats")
    )
    return markup


def register_broadcast_handlers(bot):
    """Регистрируем все обработчики для рассылки и опросов"""


    waiting_for_poll = set()

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id != OWNER_ID:
            return
        bot.send_message(message.chat.id, "🔧 Админ-панель BrenkBot", reply_markup=get_admin_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data == "admin_create_poll")
    def create_poll_start(call):
        if call.from_user.id != OWNER_ID:
            return
        waiting_for_poll.add(call.from_user.id)
        bot.edit_message_text(
            "📝 Введите текст опроса, который будет разослан всем пользователям:",
            call.message.chat.id,
            call.message.message_id
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_poll)
    def receive_poll_message(message):
        if message.from_user.id != OWNER_ID:
            return

        poll_text = message.text.strip()
        if not poll_text:
            bot.send_message(message.chat.id, "❌ Текст опроса не может быть пустым!")
            return


        waiting_for_poll.discard(message.from_user.id)


        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO polls (message, created_at) VALUES (?, ?)",
                  (poll_text, datetime.now().isoformat()))
        poll_id = c.lastrowid
        conn.commit()
        conn.close()


        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("✅ Да", callback_data=f"poll_yes_{poll_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"poll_no_{poll_id}")
        )


        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT user_id FROM broadcast_users")
        users = [row[0] for row in c.fetchall()]
        conn.close()

        success = 0
        failed = 0
        for user_id in users:
            try:
                bot.send_message(user_id, poll_text, reply_markup=keyboard)
                success += 1
            except Exception as e:
                failed += 1
                logger.warning(f"Не удалось отправить опрос пользователю {user_id}: {e}")

        bot.send_message(
            message.chat.id,
            f"✅ Опрос успешно создан и разослан!\n\n"
            f"📩 Успешно отправлено: {success}\n"
            f"❌ Не доставлено: {failed}\n"
            f"🆔 ID опроса: {poll_id}",
            reply_markup=get_admin_keyboard()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith(("poll_yes_", "poll_no_")))
    def process_vote(call):
        parts = call.data.split("_")
        vote = parts[1]
        poll_id = int(parts[2])

        user_id = call.from_user.id

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute("SELECT 1 FROM poll_votes WHERE poll_id = ? AND user_id = ?", (poll_id, user_id))
        if c.fetchone():
            bot.answer_callback_query(call.id, "Ты уже голосовал!", show_alert=True)
            conn.close()
            return


        c.execute("INSERT INTO poll_votes (poll_id, user_id, vote) VALUES (?, ?, ?)",
                  (poll_id, user_id, vote))

        if vote == "yes":
            c.execute("UPDATE polls SET yes_count = yes_count + 1 WHERE id = ?", (poll_id,))
        else:
            c.execute("UPDATE polls SET no_count = no_count + 1 WHERE id = ?", (poll_id,))

        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "Голос учтён! Спасибо ♡", show_alert=True)

   
    @bot.callback_query_handler(func=lambda call: call.data == "admin_poll_stats")
    def show_poll_stats(call):
        if call.from_user.id != OWNER_ID:
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""SELECT message, yes_count, no_count 
                     FROM polls 
                     ORDER BY id DESC LIMIT 1""")
        row = c.fetchone()
        conn.close()

        if not row:
            bot.edit_message_text(
                "Опросов ещё не проводилось.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_admin_keyboard()
            )
            bot.answer_callback_query(call.id)
            return

        message_text, yes, no = row
        total_voted = yes + no

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM broadcast_users")
        total_users = c.fetchone()[0]
        conn.close()

        stats = f"""
📊 **Результаты последнего опроса**

{message_text}

✅ Да: {yes}
❌ Нет: {no}
🗳 Всего проголосовало: {total_voted}
👥 Всего пользователей: {total_users}
        """.strip()

        bot.edit_message_text(
            stats,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
        bot.answer_callback_query(call.id)

    print("[BROADCAST] Обработчики рассылки и опросов зарегистрированы")