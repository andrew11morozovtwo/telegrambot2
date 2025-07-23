
# Telegram OpenAI Bot

Бот для Telegram, который автоматически комментирует посты с помощью OpenAI GPT.

## Быстрый старт

### 1. Клонирование репозитория
```
git clone <URL_репозитория>
cd telegrambot2
```

### 2. Установка зависимостей
```
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл `.env` в папке проекта:
```
TELEGRAM_BOT_TOKEN1=ваш_токен_бота
OPENAI_API_KEY=ваш_openai_api_key
```

### 4. Запуск бота из терминала
```
python bot.py
```

### 5. Запуск в Docker
```
docker build -t telegrambot2 .
docker run -d -e TELEGRAM_BOT_TOKEN1=ваш_токен -e OPENAI_API_KEY=ваш_openai_api_key --name telegrambot2 telegrambot2
```

## Файлы проекта
- `bot.py` — основной код бота
- `requirements.txt` — зависимости
- `.env` — переменные окружения (не добавляйте в git)
- `.dockerignore` — исключения для Docker
- `README.md` — эта инструкция

## Развитие проекта
- Добавьте сюда описание новых функций, инструкций и особенностей по мере развития проекта.
