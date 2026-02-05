# Telegram Analytics Bot

A Telegram bot that answers analytics questions about video data using natural language. The bot converts Russian questions into SQL queries using a Large Language Model (DeepSeek via OpenRouter) and executes them against PostgreSQL.

## Features

- Natural language queries in Russian about video statistics
- Automatic SQL generation with multi-layer security validation
- SELECT-only enforcement preventing data modification
- Docker deployment with automatic migrations and data loading
- Comprehensive test suite (33 tests)
- Rate limiting and configurable timeouts

## Requirements

- Python 3.11 or higher
- PostgreSQL 14 or higher
- OpenRouter API account
- Telegram Bot Token

## Quick Start

### Installation

```bash
git clone <repository-url>
cd analytics-bot
make install
```

### Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/analytics_bot
TELEGRAM_TOKEN=your-telegram-bot-token
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=deepseek/deepseek-chat
```

Obtain the required tokens:
- Telegram: Message [@BotFather](https://t.me/botfather) to create a bot
- OpenRouter: Register at [openrouter.ai](https://openrouter.ai) to get an API key

### Database Setup

```bash
# Create the database
createdb analytics_bot

# Load sample data (automatically runs migrations)
make load-data
```

### Running the Bot

Local development:
```bash
make run-bot
```

Using Docker:
```bash
docker-compose up -d
```

The Docker container automatically runs migrations and loads data on first startup.

## Usage

Once the bot is running, start a chat with it on Telegram and ask questions in Russian:

| Question | Expected Result |
|----------|-----------------|
| "Сколько всего видео?" | Total number of videos |
| "Сколько просмотров было 1 декабря?" | Total views on December 1st |
| "Какое максимальное количество лайков?" | Maximum likes on any video |
| "Сколько всего комментариев?" | Total comments across all videos |

## Architecture

The data flow follows this pattern:

1. User sends a question in Russian via Telegram
2. Bot receives the message and applies rate limiting
3. Question is sent to OpenRouter LLM (DeepSeek) with schema context
4. Generated SQL passes through 4-layer validation
5. Validated SQL is executed against PostgreSQL
6. Single numeric result is returned to the user

### Database Schema

**videos table** - Stores aggregate statistics per video
- `id` (UUID, primary key)
- `creator_id` (UUID, indexed)
- `views_count`, `likes_count`, `comments_count`, `reports_count` (BIGINT)
- `video_created_at`, `created_at`, `updated_at` (TIMESTAMPTZ)

**video_snapshots table** - Hourly measurements for trend analysis
- `id` (UUID, primary key)
- `video_id` (UUID, foreign key to videos.id)
- `views_count`, `likes_count`, `comments_count`, `reports_count` (BIGINT)
- `delta_views_count`, `delta_likes_count`, `delta_comments_count`, `delta_reports_count` (BIGINT) - change since previous snapshot
- `created_at` (TIMESTAMPTZ, indexed)

The delta columns enable efficient daily growth calculations without joining multiple rows.

## Testing

Run the test suite:

```bash
# Unit tests only (fast, no external API calls)
make test

# With coverage report
PYTHONPATH=. uv run pytest tests/ -v --cov=app

# Integration tests (requires API key and database)
export $(cat .env | grep -v '^#' | xargs)
PYTHONPATH=. uv run pytest tests/test_llm_integration.py -v
```

Test coverage includes:
- SQL guardrail validation
- Prompt template structure
- LLM SQL generation
- End-to-end query execution
- Error handling for edge cases

## Security

### SQL Injection Protection

The system implements a 4-layer validation approach:

1. **Extraction**: Parse SQL from markdown code fences or surrounding text
2. **SELECT-only**: Verify query starts with SELECT statement
3. **Forbidden Keywords**: Block INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE
4. **Aggregate Requirement**: Ensure presence of COUNT, SUM, AVG, MIN, or MAX functions

All validation failures raise `SqlValidationError` and return a generic error message to the user.

### Rate Limiting

Per-user rate limiting prevents API abuse. Default is 3 seconds between requests from the same user. Configure via `RATE_LIMIT_SECONDS` environment variable.

### Error Handling

Users receive generic error messages:
> "Ошибка обработки запроса. Попробуйте переформулировать."

Detailed error information is logged server-side with structured logging.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL async connection string |
| `TELEGRAM_TOKEN` | Yes | - | Bot token from @BotFather |
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API authentication key |
| `OPENROUTER_MODEL` | No | deepseek/deepseek-chat | LLM model identifier |
| `LLM_TIMEOUT` | No | 30 | Maximum wait time for LLM response (seconds) |
| `DB_TIMEOUT` | No | 10 | Maximum wait time for database query (seconds) |
| `RATE_LIMIT_SECONDS` | No | 3 | Minimum seconds between user requests |

## Project Structure

```
analytics-bot/
├── app/                      # Application code
│   ├── main.py              # Telegram bot entrypoint
│   ├── config.py            # Pydantic settings
│   ├── db.py                # Database connection management
│   ├── models.py            # SQLAlchemy ORM models
│   ├── llm.py               # OpenRouter client with retries
│   ├── prompt.py            # LLM prompt templates
│   ├── sql_guard.py         # SQL validation layer
│   └── query_executor.py    # SQL execution with safety checks
├── migrations/              # Alembic database migrations
├── scripts/                 # Utility scripts
│   ├── load_data.py         # JSON data loader
│   ├── test_llm.py          # Standalone LLM test
│   ├── test_query.py        # End-to-end test
│   └── entrypoint.sh        # Docker startup script
├── tests/                   # Test suite
│   ├── test_prompt.py       # Prompt validation tests
│   ├── test_sql_guard.py    # SQL guardrail tests
│   └── test_llm_integration.py  # Integration tests
├── data/                    # Sample data
│   └── videos.json
├── docker-compose.yml       # Docker orchestration
├── Dockerfile               # Bot container image
├── Makefile                 # Development commands
└── README.md                # This file
```

## Docker Deployment

The docker-compose configuration includes two services:

- **postgres**: PostgreSQL 16 with persistent volume
- **bot**: Python application with automatic migrations

Commands:
```bash
# Build and start services
docker-compose up -d

# View bot logs
docker-compose logs -f bot

# Stop all services
docker-compose down

# Restart bot only
docker-compose restart bot
```

On first startup, the bot container:
1. Waits for PostgreSQL to be healthy
2. Runs Alembic migrations
3. Loads data/videos.json if the videos table is empty
4. Starts the Telegram bot

## Development

### Code Quality

The project uses:
- **ruff**: Fast Python linter
- **mypy**: Static type checking (strict mode)
- **pytest**: Testing framework with asyncio support

Run quality checks:
```bash
make lint        # Run ruff
make typecheck   # Run mypy
make format      # Auto-format code
```

### Adding Features

To extend the bot with new query types:

1. Update `app/prompt.py` with new schema documentation if needed
2. Add example queries to the prompt template
3. Write tests in `tests/test_llm_integration.py`
4. Update this README with new usage examples

## Troubleshooting

### Bot not responding
- Verify `TELEGRAM_TOKEN` is correct
- Check bot is running: `docker-compose ps`
- View logs: `docker-compose logs -f bot`

### SQL errors
- Enable debug logging to see generated SQL
- Check database connection string
- Verify migrations ran: `uv run alembic current`

### LLM not generating valid SQL
- Check `OPENROUTER_API_KEY` is valid
- Verify model name is correct
- Review rate limits on OpenRouter dashboard

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome. Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For bug reports and feature requests, please use GitHub Issues.
