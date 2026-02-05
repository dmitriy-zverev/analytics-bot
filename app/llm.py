from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.prompt import build_prompt
from app.sql_guard import SqlValidationError, validate_sql


class SqlGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class LlmResponse:
    sql: str


class OpenRouterClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_model
        self._base_url = "https://openrouter.ai/api/v1"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def generate_sql(self, user_question: str) -> LlmResponse:
        prompt = build_prompt(user_question)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "Ты генерируешь SQL для PostgreSQL."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }

        async with httpx.AsyncClient(base_url=self._base_url, timeout=30.0) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        try:
            raw_sql = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise SqlGenerationError("Invalid LLM response format") from exc

        try:
            cleaned = validate_sql(raw_sql)
        except SqlValidationError as exc:
            raise SqlGenerationError(f"SQL validation failed: {exc}") from exc

        return LlmResponse(sql=cleaned)
