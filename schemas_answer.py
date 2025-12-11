"""Схема ответа агента"""
from pydantic import BaseModel


class Answer(BaseModel):
    """Модель ответа агента"""
    text: str
    relevant_docs: dict[str, dict[str, str]] = {}
    context: str = ''
    score: str = ''
    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0
    tokens_used: int = 0
