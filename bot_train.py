import os
import logging
from bot import main as bot_main

# Установите тестовый токен прямо здесь (замените на свой тестовый токен)
TEST_TELEGRAM_BOT_TOKEN = 'ВАШ_ТЕСТОВЫЙ_ТОКЕН'
TEST_OPENAI_API_KEY = 'ВАШ_ТЕСТОВЫЙ_OPENAI_API_KEY'

# Переопределяем переменные окружения для теста
os.environ['TELEGRAM_BOT_TOKEN1'] = TEST_TELEGRAM_BOT_TOKEN
os.environ['OPENAI_API_KEY'] = TEST_OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    print('Запуск тренировочного бота...')
    bot_main() 