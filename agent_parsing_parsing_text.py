"""Парсинг текста и JSON"""
from json import JSONDecodeError
import re
import json


def parsing_input(text_llm: str) -> json or str:
    """
    Парсит текст, содержащий json от LLM
    """
    r_re = r"```json(.*?)```"
    if re.search(r_re, text_llm, re.DOTALL):
        search = re.search(r_re, text_llm, re.DOTALL)
        text_llm = search.group(1)
    try:
        text_llm = text_llm.replace("`", "")
        text_llm = json.loads(str(text_llm))
    except JSONDecodeError:
        text_llm = "Нужно вывести корректный ввод в json формате"
    return text_llm


def parsing_html(text_llm: str) -> str:
    """
    Парсит текст, содержащий markdown от LLM
    """
    r_re = r"```markdown(.*?)```"
    if re.search(r_re, text_llm, re.DOTALL):
        search = re.search(r_re, text_llm, re.DOTALL)
        text_llm = search.group(1)
    return text_llm
