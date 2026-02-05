import asyncio
import sys

from dotenv import load_dotenv

from app.llm import OpenRouterClient


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/test_llm.py '<question>'")

    load_dotenv()
    question = " ".join(sys.argv[1:])
    client = OpenRouterClient()
    response = await client.generate_sql(question)
    print(response.sql)


if __name__ == "__main__":
    asyncio.run(main())
