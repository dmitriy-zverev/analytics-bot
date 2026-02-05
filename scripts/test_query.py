import asyncio
import sys

from dotenv import load_dotenv

from app.llm import OpenRouterClient, SqlGenerationError
from app.query_executor import QueryExecutor, SqlExecutionError


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/test_query.py '<question>'")

    load_dotenv()
    question = " ".join(sys.argv[1:])

    llm = OpenRouterClient()
    executor = QueryExecutor()
    try:
        response = await llm.generate_sql(question)
        print(f"SQL: {response.sql}")
        result = await executor.fetch_scalar(response.sql)
        print(f"Result: {result.value}")
    except (SqlGenerationError, SqlExecutionError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
    finally:
        await executor.close()


if __name__ == "__main__":
    asyncio.run(main())
