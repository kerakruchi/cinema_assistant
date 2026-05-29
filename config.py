import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Hugging Face
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"

# Server
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Настройки генерации
MAX_HISTORY_MESSAGES = 10  # кол-во сообщений в контексте
MAX_NEW_TOKENS = 1024      # максимальная длина ответа
TEMPERATURE = 0.7           # креативность (0.1-1.0)
