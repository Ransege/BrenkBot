import os
import logging
from handlers import register_handlers
from telebot import TeleBot
from dotenv import load_dotenv


load_dotenv()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")
if OWNER_ID == 0:
    raise ValueError("OWNER_ID не найден или указан неправильно в .env файле!")

bot = TeleBot(TOKEN)


register_handlers(bot, OWNER_ID)

if __name__ == '__main__':
    logger.info(f"Бот запущен. Владелец: {OWNER_ID}")
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        logger.error(f"Бот упал: {e}")