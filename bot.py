import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, PORT, WEBHOOK_URL
from llm import llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Хранилище истории (в памяти; для продакшена — Redis)
user_histories: dict[int, list[dict]] = {}


def get_history(user_id: int) -> list[dict]:
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🎬 <b>Привет! Я — КиноЭксперт</b>\n\n"
        "Я знаю всё об индустрии кино в России:\n"
        "▪️ Производство и дистрибуция\n"
        "▪️ Кинотеатры и стриминги\n"
        "▪️ Фестивали и награды\n"
        "▪️ Финансирование и законы\n"
        "▪️ История от СССР до наших дней\n\n"
        "Просто задай вопрос! 💬"
    )


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id
    user_histories.pop(user_id, None)
    await message.answer("🗑 История диалога очищена. Начинаем сначала!")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — Приветствие\n"
        "/clear — Очистить историю\n"
        "/help — Эта справка\n\n"
        "💡 Можешь просто писать вопросы про кино!"
    )


@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    history = get_history(user_id)

    history.append({"role": "user", "content": message.text})

    thinking = await message.reply("🎬 Думаю над ответом...")

    try:
        answer = await llm_client.generate(history)

        history.append({"role": "assistant", "content": answer})

        # Ограничиваем историю
        if len(history) > 20:
            user_histories[user_id] = history[-16:]

        await thinking.delete()
        await message.answer(answer)

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        await thinking.delete()
        await message.answer("⚠️ Произошла ошибка. Попробуй ещё раз.")


# ──── Запуск ────

async def on_startup():
    if WEBHOOK_URL:
        await bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            drop_pending_updates=True,
        )
        logger.info(f"Webhook set to {WEBHOOK_URL}/webhook")
    else:
        logger.info("Running in polling mode (local dev)")


async def on_shutdown():
    await bot.session.close()


async def main():
    from aiogram.webhook.aiohttp_server import SimpleRequestDispatcher, setup_application
    from aiohttp import web

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if WEBHOOK_URL:
        # Режим webhook (Render)
        app = web.Application()
        handler = SimpleRequestDispatcher(dispatcher=dp, bot=bot, handle_in_background=False)
        handler.register(app, "/webhook")
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
        await site.start()
        logger.info(f"Webhook server started on port {PORT}")

        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            await runner.cleanup()
    else:
        # Режим polling (локальная разработка)
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
