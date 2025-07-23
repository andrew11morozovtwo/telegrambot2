import os
import json
import csv
from datetime import datetime
import logging
import traceback
import nest_asyncio


from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена Telegram API из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN1')
if not TOKEN:
    logging.critical("Необходимо установить переменную окружения TELEGRAM_BOT_TOKEN1 с токеном вашего бота!")
    exit(1)

# Получение API-ключа OpenAI из переменной окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.critical("Необходимо установить переменную окружения OPENAI_API_KEY с вашим API-ключом!")
    exit(1)

# Инициализация клиента OpenAI
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)

DEFAULT_RESPONSE_LIMIT = 9

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот, который комментирует Ваши посты с помощью API OpenAI. Версия 15 января 2025 года. По умолчанию до 9 комментариев на пост.")

async def help_command(update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    Чтобы использовать этого бота, выполните следующие шаги:

    1. Добавьте бота в качестве администратора в ваш телеграмм-канал и в чат обсуждения.
    2. Прокомментируйте или дождитесь комментария на любой пост в канале.
    3. Бот автоматически прокомментирует ваш пост с помощью API OpenAI.
    4. Бот будет комментировать до 9 раз каждый пост (по умолчанию).
    5. В конце комментария бот добавит фразу "Комментарий подготовлен ботом-администратором с использованием искусственного интеллекта".
    6. Чтобы изменить количество ответов бота, используйте команду /setlimit <число>.
    7. Чтобы отключить ответы бота, используйте команду /mute.
    8. Чтобы включить ответы бота, используйте команду /unmute.

    Если у вас возникнут вопросы, напишите /start, чтобы получить информацию о боте.
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

async def set_response_limit(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_limit = int(context.args[0])
        if new_limit < 1:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Количество ответов должно быть положительным числом больше нуля. Пример использования: /setlimit 7")
            return
        context.bot_data['response_limit'] = new_limit
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Количество ответов бота установлено на {new_limit}.")
    except (IndexError, ValueError):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, укажите корректное число. Пример использования: /setlimit 7")

async def mute(update, context: ContextTypes.DEFAULT_TYPE):
    context.bot_data['muted'] = True
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Бот теперь молчит и не будет публиковать ответы.")

async def unmute(update, context: ContextTypes.DEFAULT_TYPE):
    context.bot_data['muted'] = False
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Бот снова будет публиковать ответы.")

async def comment_post(update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    post_id = update.message.reply_to_message.message_id
    user_message = update.message.reply_to_message.caption or update.message.reply_to_message.text
    user_comment = update.message.caption or update.message.text

    if 'comments_count' not in context.user_data:
        context.user_data['comments_count'] = {}

    if post_id not in context.user_data['comments_count']:
        context.user_data['comments_count'][post_id] = 0

    response_limit = context.bot_data.get('response_limit', DEFAULT_RESPONSE_LIMIT)

    if context.user_data['comments_count'][post_id] < response_limit:
        try:
            chat_history = context.user_data.get('chat_history', {}).get(post_id, [])
            chat_history.append({"role": "user", "content": user_comment})

            messages = [
                {"role": "system", "content": "Вы — бот-администратор канала 'Я-Инженер', который делится новостями науки и техники. Ваша задача — давать краткие, вежливые и полезные комментарии к постам, общаясь с читателями от мужского лица на 'ВЫ'. Учитывайте контекст каждого поста и комментарии пользователей."},
                {"role": "user", "content": f"В телеграмм-канале 'Я-Инженер' опубликован пост: '{user_message}'. Пожалуйста, дайте краткий комментарий (не более 400 символов) и используйте эмодзи для повышения привлекательности ответа!"}
            ] + chat_history

            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=messages
            )

            comment_text = chat_completion.choices[0].message.content

            if not context.bot_data.get('muted', False):
                send_message_text = f"{comment_text}\n\nКомментарий подготовлен ботом-администратором с использованием искусственного интеллекта."
                await context.bot.send_message(chat_id=update.effective_chat.id, text=send_message_text, reply_to_message_id=update.message.reply_to_message.message_id)

            context.user_data['comments_count'][post_id] += 1
            chat_history.append({"role": "assistant", "content": comment_text})
            if 'chat_history' not in context.user_data:
                context.user_data['chat_history'] = {}
            context.user_data['chat_history'][post_id] = chat_history

            file_path = 'comments_data_ing.csv'

            if not os.path.exists(file_path):
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
                    writer.writerow([
                        "post_id", "date", "user_message", "user_comment",
                        "date_time", "serialized_chat_history", "serialized_messages",
                        "comment_text", "send_message_text"
                    ])

            with open(file_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
                serialized_chat_history = json.dumps(chat_history, ensure_ascii=False)
                serialized_messages = json.dumps(messages, ensure_ascii=False)
                current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data_to_write = [
                    post_id, datetime.now().strftime("%Y-%m-%d"), user_message,
                    user_comment, current_datetime, serialized_chat_history,
                    serialized_messages, comment_text, send_message_text
                ]
                writer.writerow(data_to_write)

        except Exception as e:
            logger.error(f"Ошибка при создании комментария: {e}\n{traceback.format_exc()}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка при создании комментария. Пожалуйста, попробуйте позже.")

def setup_application():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('setlimit', set_response_limit))
    application.add_handler(CommandHandler('mute', mute))
    application.add_handler(CommandHandler('unmute', unmute))
    application.add_handler(MessageHandler(filters.REPLY & (filters.TEXT | filters.PHOTO), comment_post))
    return application

async def main():
    application = setup_application()
    await application.run_polling()

if __name__ == '__main__':
    import sys
    import asyncio

    if sys.platform.startswith('win') and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    nest_asyncio.apply()
    asyncio.run(main()) 