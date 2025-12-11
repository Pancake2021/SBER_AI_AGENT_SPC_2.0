"""Парсинг LLM ответов"""
from agent.parsing.parsing_text import parsing_input
from agent.tools.run_giga import llm
from agent.tools.exceptions import CustomError
from agent.prompts.prompts import prompt_classification, final_classification
import json


class ParseLLM:
    """Парсинг LLM ответов"""

    def __init__(self):
        self.t_util = "Полезность: {util}\n"
        self.t_analyze = "Анализ файла: {analyze}\n"
        self.t_split = "-"*80 + "\n\n"

    def get_llm_answer(self, new_prompt: str, sys_prompt: str) -> str:
        """Получить ответ от LLM и распарсить"""
        result = None
        try:
            answer = llm(new_prompt, sys_prompt)
            answer = parsing_input(answer)
            if not isinstance(answer, dict):
                result = json.loads(answer)
            result = answer
        except CustomError:
            result = self.get_llm_answer(new_prompt, sys_prompt)
        return result

    def answer_read_file(self, query: str, prompt: str) -> str:
        """Результат чтения файла в ВВ"""
        data = llm(query, prompt)
        j = parsing_input(data)
        analize_file = j["analize_tool"]
        answer_llm = j["answer"]
        result = (
            self.t_analyze +
            self.t_util +
            self.t_split
        ).format(
            analyze=analize_file,
            util=answer_llm
        )
        return result

    def get_main_answer_agent(
        self,
        new_prompt: str,
        prompt: str,
    ) -> dict:
        """Получить действие от агента"""
        answer = self.get_llm_answer(new_prompt, prompt)
        result = {
            "Что было": answer.get("answer_tools"),
            "Мысли": answer.get("thought"),
            "Действие": answer.get("action"),
            "Инструмент": answer.get("action_input"),
        }
        return result


def classification_query(query: str, verbose=False):
    """Проверка запроса пользователя на релевантность"""
    classification = llm(query, prompt_classification)
    q = "Верни ответ на вопрос:"
    result = parsing_input(classification)
    if verbose:
        print(classification)
    if (
        isinstance(result, dict)
        and isinstance(result["classification"], str)
        and result["classification"].lower() == "релевантные"
    ):
        return query
    answer = llm(
        q, final_classification.format(data=classification)
    )
    return {"not_rel": answer}
