import asyncio

import structlog
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import get_settings
from app.llm import OpenRouterClient, SqlGenerationError
from app.query_executor import QueryExecutor, SqlExecutionError

logger = structlog.get_logger()


async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет! Отправь вопрос по аналитике видео на русском, и я верну число.",
        parse_mode=ParseMode.HTML,
    )


async def handle_query(message: Message, llm: OpenRouterClient, executor: QueryExecutor) -> None:
    question = message.text or ""
    if not question.strip():
        await message.answer("Пожалуйста, отправь текстовый вопрос.")
        return

    try:
        response = await llm.generate_sql(question)
        result = await executor.fetch_scalar(response.sql)
        await message.answer(str(result.value))
    except (SqlGenerationError, SqlExecutionError) as exc:
        logger.warning("query_failed", error=str(exc))
        await message.answer("Ошибка обработки запроса. Попробуйте переформулировать.")


async def main() -> None:
    settings = get_settings()
    bot = Bot(token=settings.telegram_token)
    dp = Dispatcher()
    llm = OpenRouterClient()
    executor = QueryExecutor()

    dp.message.register(handle_start, CommandStart())

    async def query_handler(message: Message) -> None:
        await handle_query(message, llm, executor)

    dp.message.register(query_handler, F.text)

    try:
        await dp.start_polling(bot)
    finally:
        await executor.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
