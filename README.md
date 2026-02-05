# Telegram Analytics Bot

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

## Docker Deployment

Create `.env` with your tokens:
```
TELEGRAM_TOKEN=your-telegram-token
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=deepseek/deepseek-chat
```

Build and run:
```bash
docker-compose up -d
```

On first startup, the bot will:
1. Run database migrations
2. Check if data exists
3. Load `data/videos.json` if database is empty
4. Start the Telegram bot

View logs:
```bash
docker-compose logs -f bot
```

Stop:
```bash
docker-compose down
```

## Architecture

### Overview
The bot converts Russian natural-language questions into SQL queries using an LLM, executes them against PostgreSQL, and returns numeric results.

**Flow:**
```
User Question (Russian) 
  → LLM (OpenRouter/DeepSeek) 
  → SQL Generation 
  → Validation & Guardrails 
  → PostgreSQL Execution 
  → Numeric Result 
  → Telegram Response
```

### Database Schema

#### `videos` table (aggregate video statistics)
- `id` (UUID) - video identifier
- `creator_id` (UUID) - creator identifier
- `video_created_at` (timestamptz) - when video was created
- `views_count`, `likes_count`, `comments_count`, `reports_count` (bigint) - current totals
- `created_at`, `updated_at` (timestamptz) - record timestamps

#### `video_snapshots` table (hourly measurements)
- `id` (UUID) - snapshot identifier
- `video_id` (UUID, FK) - references videos.id
- `created_at` (timestamptz) - snapshot timestamp
- `views_count`, `likes_count`, `comments_count`, `reports_count` (bigint) - snapshot values
- `delta_views_count`, `delta_likes_count`, `delta_comments_count`, `delta_reports_count` (bigint) - changes since last snapshot

**Use cases:**
- Total video count: query `videos` table
- Growth on specific day: query `video_snapshots` with `delta_*` fields filtered by date

### LLM Prompt Engineering

**System prompt** (`app/prompt.py`):
- Describes both tables with all fields and types
- Specifies strict rules for SQL generation
- Enforces single numeric output (COUNT/SUM/AVG/MIN/MAX)
- Requires aggregate functions only
- Allows only SELECT queries
- Permits JOIN only on `video_snapshots.video_id = videos.id`

**Key rules:**
1. Return ONLY SQL (no explanations)
2. Must use aggregate function (COUNT/SUM/AVG/MIN/MAX)
3. Single numeric result
4. No ID columns in output
5. Use `delta_*` for daily growth calculations

**Example prompts:**
- "Сколько всего видео?" → `SELECT COUNT(*) FROM videos`
- "Сколько просмотров набрали видео 1 декабря?" → `SELECT SUM(delta_views_count) FROM video_snapshots WHERE DATE(created_at) = '2025-12-01'`

### SQL Guardrails

**Validation layers** (`app/sql_guard.py`):

1. **Extraction**: Strip markdown code fences and extract first SELECT
2. **SELECT-only check**: Reject if doesn't start with SELECT
3. **Forbidden keywords**: Block INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/CREATE
4. **Aggregate requirement**: Ensure COUNT/SUM/AVG/MIN/MAX present

**Execution safety** (`app/query_executor.py`):
- Enforce numeric result type (int/float)
- Return 0 if NULL
- Raise custom error if non-numeric

### LLM Integration

**Provider**: OpenRouter API  
**Model**: DeepSeek Chat (configurable)  
**Temperature**: 0.0 (deterministic)  
**Retries**: 3 attempts with exponential backoff

**Error handling:**
- Invalid LLM response → `SqlGenerationError`
- SQL validation failure → `SqlGenerationError`
- Execution error → `SqlExecutionError`
- User sees: "Ошибка обработки запроса. Попробуйте переформулировать."

### Components

- `app/main.py` - Telegram bot entrypoint (aiogram)
- `app/llm.py` - OpenRouter client with retries
- `app/prompt.py` - LLM prompt template
- `app/sql_guard.py` - SQL validation and sanitization
- `app/query_executor.py` - Async PostgreSQL execution
- `app/models.py` - SQLAlchemy ORM models
- `app/config.py` - Pydantic settings
- `scripts/load_data.py` - JSON data loader
- `scripts/entrypoint.sh` - Docker startup script