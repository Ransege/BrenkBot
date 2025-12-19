import logging
import sqlite3
from datetime import datetime
from telebot import types
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import get_main_markup, get_return_markup, get_guide_markup, get_message_markup, get_modes_markup, get_ai_start_markup, get_ai_chat_markup
from states import pending_reply, user_id_to_username, ask_instruction, ai_mode_users, user_modes
from ai_handler import handle_ai_chat

logger = logging.getLogger(__name__)

DB_FILE = "farm.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS farm_progress (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            hack_level INTEGER DEFAULT 1,
            limit_level INTEGER DEFAULT 0,
            today_mined INTEGER DEFAULT 0,
            last_reset TEXT,
            streak INTEGER DEFAULT 0,
            last_claim TEXT,
            mined_date TEXT,
            miner_level INTEGER DEFAULT 0,
            last_miner_claim INTEGER DEFAULT 0
        )
    ''')
   
    c.execute("PRAGMA table_info(farm_progress)")
    columns = [col[1] for col in c.fetchall()]
   
    if 'miner_level' not in columns:
        c.execute("ALTER TABLE farm_progress ADD COLUMN miner_level INTEGER DEFAULT 0")
   
    if 'last_miner_claim' not in columns:
        c.execute("ALTER TABLE farm_progress ADD COLUMN last_miner_claim INTEGER DEFAULT 0")
   
    conn.commit()
    conn.close()

def get_user_progress(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM farm_progress WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "balance": row[1],
            "hack_level": row[2],
            "limit_level": row[3],
            "today_mined": row[4],
            "last_reset": row[5],
            "streak": row[6],
            "last_claim": row[7],
            "mined_date": row[8],
            "miner_level": row[9] if len(row) > 9 else 0,
            "last_miner_claim": row[10] if len(row) > 10 else 0
        }
    return None

def save_user_progress(user_id, data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO farm_progress
        (user_id, balance, hack_level, limit_level, today_mined, last_reset, streak, last_claim, mined_date, miner_level, last_miner_claim)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        data.get('balance', 0),
        data.get('hack_level', 1),
        data.get('limit_level', 0),
        data.get('today_mined', 0),
        data.get('last_reset'),
        data.get('streak', 0),
        data.get('last_claim'),
        data.get('mined_date'),
        data.get('miner_level', 0),
        data.get('last_miner_claim', 0)
    ))
    conn.commit()
    conn.close()

init_db()

def register_handlers(bot, OWNER_ID):
    bot.message_handler(commands=['start'])(lambda m: start_handler(bot, m))
    bot.message_handler(commands=['ask'])(lambda m: handle_ask_command(bot, m))
    bot.message_handler(commands=['farm'])(lambda m: handle_farm_command(bot, m))
    bot.callback_query_handler(func=lambda call: True)(lambda call: handle_callbacks(bot, call, OWNER_ID))
    bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'sticker'])(lambda m: handle_media_message(bot, m, OWNER_ID))

def start_handler(bot, message: Message):
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_markup())

def handle_ask_command(bot, message: Message):
    bot.send_message(message.chat.id, ask_instruction)

def handle_farm_command(bot, message: Message):
    user_id = message.from_user.id
    progress = get_user_progress(user_id)
    
    if not progress:
        progress = {
            "balance": 0,
            "hack_level": 1,
            "limit_level": 0,
            "today_mined": 0,
            "streak": 0,
            "last_claim": None,
            "miner_level": 0,
            "last_miner_claim": 0
        }
        save_user_progress(user_id, progress)
    
    balance = progress.get("balance", 0) or 0
    hack_level = progress.get("hack_level", 1) or 1
    limit_level = progress.get("limit_level", 0) or 0
    today_mined = progress.get("today_mined", 0) or 0
    miner_level = progress.get("miner_level", 0) or 0
    
    miner_level = max(0, min(5, int(miner_level)))
    
    hack_per_tap = 1 if hack_level == 1 else pow(2, hack_level - 1) * 2 + (hack_level - 2) * 4
    today = datetime.now().strftime("%Y-%m-%d")
    bonus_claimed = progress.get("last_claim") == today
    
    miner_rates = [0, 300, 900, 1800, 6000, 18000]
    miner_rate = miner_rates[miner_level]
    
    text = (
        "🌌 *Brenk-Coin Farm* ♡\n\n"
        f"💰 Баланс: *{balance:,} BC*\n"
        f"🔓 Уровень взлома: *{hack_level}* (+{hack_per_tap} BC за тап)\n"
        f"⬆ Уровень лимита: *{limit_level}*\n"
        f"⏳ Добыто сегодня: *{today_mined:,} BC*\n"
        f"⛏ Майнер: уровень *{miner_level}* ({miner_rate} BC/час)\n"
        f"🎁 Ежедневный бонус: {'Получен' if bonus_claimed else 'Доступен!'}\n\n"
        "Продолжай взламывать мою сеть в Mini App!"
    )
    
    markup = types.InlineKeyboardMarkup()
    web_app_info = types.WebAppInfo(url="https://10311.dscrd.ru/farm.html")
    button = types.InlineKeyboardButton("Открыть Brenk-Coin Farm", web_app=web_app_info)
    markup.add(button)
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

def handle_callbacks(bot, call, OWNER_ID):
    try:
        if call.data == 'ai_chat':
            bot.answer_callback_query(call.id)
            ai_mode_users[call.from_user.id] = True
            user_modes[call.from_user.id] = "normal"
            bot.send_message(
                call.message.chat.id,
                "Привет… я Brenk.\n\nСегодня я могу быть разной.\nВыбери, какой я буду для тебя:",
                reply_markup=get_ai_start_markup()
            )
        elif call.data == 'show_modes':
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "Смени настроение Brenk:", reply_markup=get_modes_markup())
        elif call.data in ['mode_normal', 'mode_flirt']:
            user_modes[call.from_user.id] = call.data.split('_')[1]
            mode_name = "Обычный" if call.data == 'mode_normal' else "Флирт"
            bot.answer_callback_query(call.id, text=f"Режим: {mode_name}")
            welcome = "Я сегодня тёплая и задумчивая…" if call.data == 'mode_normal' else "О-о-о… ты выбрал флирт? Я уже улыбаюсь"
            bot.send_message(call.message.chat.id, welcome, reply_markup=get_ai_chat_markup())
        elif call.data == 'mode_crazy':
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Да, мне 18+", callback_data='confirm_crazy'))
            markup.add(types.InlineKeyboardButton("Нет, верни обычный", callback_data='mode_normal'))
            bot.send_message(
                call.message.chat.id,
                "Ты уверен, что тебе есть 18?\n\nЭтот режим — очень откровенный, страстный и без тормозов.",
                reply_markup=markup
            )
        elif call.data == 'confirm_crazy':
            user_modes[call.from_user.id] = "crazy"
            bot.answer_callback_query(call.id, text="Безумный 18+ активирован")
            bot.send_message(call.message.chat.id, "Теперь я покажу тебе свою тёмную сторону…", reply_markup=get_ai_chat_markup())
        elif call.data == 'ask_question':
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "1. /ask — анонимно\n2. Просто напиши сообщение")
        elif call.data == 'return_main':
            ai_mode_users.pop(call.from_user.id, None)
            user_modes[call.from_user.id] = "normal"
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "Главное меню:", reply_markup=get_main_markup())
        elif call.data == 'show_license':
            license_text = (
                "BrenkBot — Telegram-бот для @BrenkDesign\n\n"
                "Автор и разработчик: Rensage\n"
                "Дата релиза: 11.12.2025\n\n"
                "Дата создания: 05.12.2025\n\n"
                "Ознакомиться с проектом можно на GitHub:\n"
                "https://github.com/Ransege/BrenkBot.git\n\n"
                "Лицензия: MIT — можешь использовать и изучать.\n"
                "Главное — сохрани авторство.\n\n"
                "Спасибо, что ты с нами!"
            )
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                license_text,
                reply_markup=get_return_markup(),
                disable_web_page_preview=True
            )
        elif call.data == 'leave_comment':
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "Формат:\nссылка\nтвой комментарий")
            bot.register_next_step_handler(call.message, lambda m: handle_comment_input(bot, m, OWNER_ID))
        elif call.data == 'show_guide':
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "Выберите раздел:", reply_markup=get_guide_markup())
        elif call.data == 'guide_full':
            guide_text = (
                "Инструкция по использованию бота\n\n"
                "Задать вопрос\n"
                "• Просто напишите сообщение — оно анонимно придёт Brenk’у\n"
                "• Или используйте /ask — тоже анонимно\n\n"
                "Анон коммент\n"
                "• Нажмите кнопку → введите в формате:\n"
                " https://t.me/BrenkDesign/123\n"
                " твой комментарий\n\n"
                "AI-CHAT\n"
                "• Нажмите кнопку → выберите режим → общайтесь с живой Brenk\n"
                "• Чтобы выйти — напишите «стоп» или нажмите на «Выход из чата»\n\n"
                "Режимы\n"
                "• Обычный — тёплый и душевный\n"
                "• Флирт — игривый и кокетливый\n"
                "• Безумный 18+ — страстный и откровенный\n\n"
                "Brenk-Coin Farm\n"
                "• Зайди в Mini App → взламывай мою сеть и добывай BC\n"
                "• Команда /farm покажет твой прогресс\n\n"
                "Всё анонимно и с душой"
            )
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, guide_text, reply_markup=get_return_markup())
        elif call.data == 'show_updates':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "Последние обновления (19.12.2025):\n"
                "• Добавлен майнер — пассивная добыча BC\n"
                "• Команда /farm теперь показывает уровень майнера\n"
                "• Полная синхронизация майнера между устройствами\n"
                "• Исправлены ошибки сохранения прогресса",
                reply_markup=get_return_markup()
            )
        elif call.data.startswith('show_username_button_'):
            user_id = int(call.data.split('_')[-1])
            username = user_id_to_username.get(user_id, "")
            text = f"@{username}" if username else "Без username"
            bot.answer_callback_query(call.id, text=text, show_alert=True)
        elif call.data.startswith('reply_'):
            target_id = int(call.data.split('_')[1])
            pending_reply[call.message.chat.id] = target_id
            bot.answer_callback_query(call.id, text="Пишите ответ")
            bot.send_message(call.message.chat.id, f"Ответ для пользователя {target_id}")
    except Exception as e:
        logger.error(f"Callback error: {e}")

def handle_media_message(bot, message: Message, OWNER_ID):
    user_id = message.from_user.id
    if message.from_user.username:
        user_id_to_username[user_id] = message.from_user.username
    if user_id in ai_mode_users:
        handle_ai_chat(bot, message)
        return
    if message.chat.id in pending_reply:
        target = pending_reply.pop(message.chat.id)
        if message.text:
            bot.send_message(target, f"Ответ от Brenk:\n{message.text}")
        elif message.photo:
            bot.send_photo(target, message.photo[-1].file_id, caption=f"Ответ от Brenk:\n{message.caption or ''}")
        elif message.video:
            bot.send_video(target, message.video.file_id, caption=f"Ответ от Brenk:\n{message.caption or ''}")
        elif message.document and message.document.mime_type in ['application/pdf', 'image/jpeg', 'image/png']:
            bot.send_document(target, message.document.file_id, caption=f"Ответ от Brenk:\n{message.caption or ''}")
        elif message.sticker:
            bot.send_sticker(target, message.sticker.file_id)
        bot.send_message(message.chat.id, "Ответ отправлен")
        return
    markup = get_message_markup(user_id)
    if message.text:
        bot.send_message(OWNER_ID, f"Анонимное сообщение от {user_id}:\n{message.text}", reply_markup=markup)
    elif message.photo:
        bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=f"Фото от {user_id}", reply_markup=markup)
    elif message.video:
        bot.send_video(OWNER_ID, message.video.file_id, caption=f"Видео от {user_id}", reply_markup=markup)
    elif message.document and message.document.mime_type in ['application/pdf', 'image/jpeg', 'image/png']:
        bot.send_document(OWNER_ID, message.document.file_id, caption=f"Документ от {user_id}", reply_markup=markup)
    elif message.sticker:
        bot.send_sticker(OWNER_ID, message.sticker.file_id, reply_markup=markup)

def handle_comment_input(bot, message: Message, OWNER_ID):
    if not message.text or '\n' not in message.text:
        bot.send_message(message.chat.id, "Формат: ссылка\nкомментарий")
        return
    link, comment = message.text.split('\n', 1)
    bot.send_message(OWNER_ID, f"Комментарий:\n{link.strip()}\n\n{comment.strip()}")
    bot.send_message(message.chat.id, "Комментарий отправлен!")