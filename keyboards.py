from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Задать вопрос", callback_data='ask_question'),
        InlineKeyboardButton("Анон коммент", callback_data='leave_comment'),
        InlineKeyboardButton("Инструкция", callback_data='show_guide'),
        InlineKeyboardButton("Обновления", callback_data='show_updates'),
        InlineKeyboardButton("AI-CHAT", callback_data='ai_chat'),
    )
    return markup

def get_return_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data='return_main'))
    return markup

def get_guide_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Как пользоваться ботом", callback_data='guide_full'),
        InlineKeyboardButton("Обновления", callback_data='show_updates')
    )
    markup.add(InlineKeyboardButton("Назад", callback_data='return_main'))
    return markup


def get_ai_start_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Обычный", callback_data='mode_normal'),
        InlineKeyboardButton("Флирт", callback_data='mode_flirt'),
        InlineKeyboardButton("Безумный 18+", callback_data='mode_crazy'),
        InlineKeyboardButton("Назад в меню", callback_data='return_main')
    )
    return markup


def get_ai_chat_markup():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Сменить режим", callback_data='show_modes'),
        InlineKeyboardButton("Выход из чата", callback_data='return_main')
    )
    return markup

def get_modes_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Обычный", callback_data='mode_normal'),
        InlineKeyboardButton("Флирт", callback_data='mode_flirt'),
        InlineKeyboardButton("Безумный 18+", callback_data='mode_crazy'),
        InlineKeyboardButton("Назад", callback_data='return_main')
    )
    return markup

def get_message_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Показать @Username", callback_data=f'show_username_button_{user_id}'))
    markup.add(InlineKeyboardButton("Ответить", callback_data=f'reply_{user_id}'))
    return markup