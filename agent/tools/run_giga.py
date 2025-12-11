"""Вызов GigaChat API"""
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_community.chat_models.gigachat import GigaChat
from langchain_community.chat_models.gigachat import _convert_dict_to_message
from gigachat.exceptions import ResponseError
from agent.tools.exceptions import BlackList
from typing import Any
from time import sleep
from pathlib import Path
import os
import json


def ignore_error(func, *args, **kwargs):
    """Ингорирование ошибки к requests с retry механизмом"""
    attempts = 0
    while True:
        try:
            result = func(*args, **kwargs)
            return result
        except ResponseError as e:
            attempts += 1
            if attempts >= 10:
                raise e
            sleep(1)
        except BlackList as e:
            raise BlackList("Невозможно обработать запрос. Система blacklist") from e
        except Exception as e:  # pylint:disable=broad-exception-caught
            attempts += 1
            if attempts >= 10:
                raise e
            sleep(1)


class CustomGigaChat(GigaChat):
    """Custom Giga Chat с обработкой ошибок"""

    def _generate(self, *args, **kwargs):
        result = ignore_error(super()._generate, *args, **kwargs)
        return result

    def _create_chat_result(self, response: Any) -> ChatResult:
        generations = []
        for res in response.choices:
            message = _convert_dict_to_message(res.message)
            finish_reason = res.finish_reason

            gen = ChatGeneration(
                message=message,
                generation_info={"finish_reason": finish_reason},
            )
            generations.append(gen)
            if finish_reason != "stop":
                raise BlackList("Finish reason не 'stop'")
        llm_output = {
            "token_usage": response.usage,
            "model_name": response.model
        }
        return ChatResult(generations=generations, llm_output=llm_output)


def write_tokens(pr, com, to):
    """Сохранение статистики токенов в JSON"""
    file_path = Path("/home/datalab/nfs/json_tokens.json")
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            new_data = {
                "prompt_tokens": data["prompt_tokens"] + pr,
                "completion_tokens": data["completion_tokens"] + com,
                "total_tokens": data["total_tokens"] + to
            }
            with open("/home/datalab/nfs/json_tokens.json", "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
    else:
        with open("/home/datalab/nfs/json_tokens.json", "w", encoding="utf-8") as f:
            json.dump({
                "prompt_tokens": pr,
                "completion_tokens": com,
                "total_tokens": to
            }, f, ensure_ascii=False, indent=2)


def llm(query, prompt, model_name="GigaChat-2-Max", temperature=0.35):
    """Главная функция для вызова GigaChat"""
    chat = CustomGigaChat(
        base_url="http://liveaccess/v1/gc",
        access_token=os.environ.get("JPY_API_TOKEN"),
        model=model_name,
        temperature=temperature
    )
    message = [
        SystemMessage(content=prompt)
    ]
    message.append(HumanMessage(content=query))
    result = chat.invoke(message)
    prompt_tokens = result.response_metadata["token_usage"].prompt_tokens
    completion_tokens = result.response_metadata["token_usage"].completion_tokens
    total_tokens = result.response_metadata["token_usage"].total_tokens
    write_tokens(prompt_tokens, completion_tokens, total_tokens)
    return result.content
