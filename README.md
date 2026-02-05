# analytics-bot

Async Telegram bot for video analytics on top of PostgreSQL.

## Requirements
- Python 3.11+
- PostgreSQL
- OpenRouter API key
- Telegram bot token

## Setup
```bash
make install
```

Create `.env` (see `.env` template):
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/analytics_bot
TELEGRAM_TOKEN=your-telegram-token
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=deepseek/deepseek-chat
```

## Migrations & Data Load
```bash
make load-data
```
This runs Alembic migrations and loads `data/videos.json`.

## LLM SQL Test
```bash
PYTHONPATH=. uv run python scripts/test_llm.py "Сколько всего видео есть в системе?"
```

## End-to-end Query Test (LLM → SQL → DB)
```bash
PYTHONPATH=. uv run python scripts/test_query.py "Сколько всего видео есть в системе?"
```

## Run Bot
```bash
make run-bot
```

The bot accepts Russian questions and replies with a single numeric value.