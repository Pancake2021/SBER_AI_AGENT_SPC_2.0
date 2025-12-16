"""Память и состояние агента"""
from typing_extensions import TypedDict
from agent.parsing.parsing_llm import ParseLLM


class State(ParseLLM):
    """Сборщик результатов от tools и LLM"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thought = ""
        self.final = None
        self.count_steps = 0
        self.relevant_doc = {}
        self.texts = ""
        self.score = ""
        self.history_tools = {}
        self.result_tools = {}
        self.prompt_tokens = -1
        self.completion_tokens = -1
        self.total_tokens = -1
        
        # Conversation Memory
        self.conversation_summary = ""
        self.conversation_history = []

    def count_add(self) -> None:
        """Увеличить счётчик шагов"""
        self.count_steps += 1

    def count_tokens(self, data: dict) -> None:
        """Накопить статистику токенов"""
        if data.get("prompt_tokens"):
            self.prompt_tokens += data.get("prompt_tokens")
        if data.get("completion_tokens"):
            self.completion_tokens += data.get("completion_tokens")
        if data.get("total_tokens"):
            self.total_tokens += data.get("total_tokens")


class AgentState(TypedDict):
    """Вывод конечного результата от Stage"""
    user_query: str
    list_tools: dict
    final_answer: dict
    pars_quest: State


def should_continue(state: State) -> str:
    """Условие для агента - проверить финальный ответ"""
    if state["pars_quest"].final:
        return "success"
    return "failed"
