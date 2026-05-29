import aiohttp
from config import HF_API_TOKEN, HF_MODEL, MAX_NEW_TOKENS, TEMPERATURE, MAX_HISTORY_MESSAGES

SYSTEM_PROMPT = """Ты — эксперт по индустрии кино в России. Твоя специальность:

🎬 Российское кинопроизводство — студии, режиссёры, продюсеры
📊 Кинотеатральный рынок — сборы, дистрибуция, показы
🏆 Фестивали — Кинотавр, ММКФ, Оскар и российские премии
📜 Законодательство — Фонд кино, ЕАИС, возрастная маркировка
💰 Финансирование — гос. поддержка, частные инвестиции, краудфандинг
📺 Стриминговые платформы — Кинопоиск, Иви, Okko, Premier
🎭 История российского кино — от СССР до наших дней
🌟 Актёры и их карьера — российские звёзды, новые лица

Отвечай подробно, но структурированно. Используй примеры и цифры,
когда это уместно. Если не уверен в данных — честно скажи об этом.
Отвечай на русском языке."""


class LLMClient:
    def __init__(self):
        self.api_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        self.headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json",
        }

    def _build_messages(self, history: list[dict]) -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        recent = history[-MAX_HISTORY_MESSAGES:]
        messages.extend(recent)
        return messages

    async def generate(self, history: list[dict]) -> str:
        messages = self._build_messages(history)

        payload = {
            "model": HF_MODEL,
            "messages": messages,
            "max_tokens": MAX_NEW_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": 0.9,
            "stream": False,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                elif response.status == 503:
                    return (
                        "⏳ Модель сейчас загружается на сервере. "
                        "Попробуй отправить вопрос через 20-30 секунд."
                    )
                else:
                    error_text = await response.text()
                    print(f"HF API Error {response.status}: {error_text}")
                    return "❌ Произошла ошибка при обращении к модели. Попробуй позже."


# Глобальный экземпляр
llm_client = LLMClient()
