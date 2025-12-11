"""Вызов GigaChat API"""
from langchain_core.messages import HumanMessage, SystemMessage
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
    # Используем локальный файл в текущей директории
    file_path = Path("json_tokens.json")
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
            new_data = {
                "prompt_tokens": data.get("prompt_tokens", 0) + pr,
                "completion_tokens": data.get("completion_tokens", 0) + com,
                "total_tokens": data.get("total_tokens", 0) + to
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({
                "prompt_tokens": pr,
                "completion_tokens": com,
                "total_tokens": to
            }, f, ensure_ascii=False, indent=2)


def llm(query, prompt, model_name="GigaChat-2-Max", temperature=0.35):
    """Главная функция для вызова GigaChat"""
    
    # Проверяем наличие внутреннего токена
    jpy_token = os.environ.get("JPY_API_TOKEN")
    
    if jpy_token:
        # Внутренний контур
        base_url = "http://liveaccess/v1/gc"
        auth_token = jpy_token
        # Для внутреннего контура часто используется access_token параметр
        kwargs = {"access_token": auth_token}
    else:
        # Внешний контур (публичный API)
        base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        # Ищем стандартные креды
        auth_token = os.environ.get("GIGACHAT_CREDENTIALS") or os.environ.get("GIGACHAT_API_KEY")
        
        if not auth_token:
            # Если токена нет, запрашиваем у пользователя
            print("\n⚠️  Токен GigaChat не найден в переменных окружения.")
            print("Пожалуйста, введите ваш Авторизационный ключ (Credentials) от GigaChat API.")
            print("Получить ключ можно здесь: https://developers.sber.ru/studio/workspace")
            
            try:
                auth_token = input("Введите GIGACHAT_CREDENTIALS: ").strip()
            except EOFError:
                # Если input невозможен (неинтерактивный режим), кидаем ошибку
                raise ValueError("Не найден токен GigaChat! Установите GIGACHAT_CREDENTIALS в .env")

            if auth_token:
                # Сохраняем в .env файл
                env_path = Path(".env")
                if not env_path.exists():
                    with open(env_path, "w", encoding="utf-8") as f:
                        f.write(f"GIGACHAT_CREDENTIALS={auth_token}\n")
                else:
                    # Проверяем, есть ли уже такая переменная
                    with open(env_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if "GIGACHAT_CREDENTIALS=" in content:
                        # Заменяем существующую (простая реализация, может быть не идеальной для сложных .env)
                        lines = content.splitlines()
                        new_lines = []
                        for line in lines:
                            if line.startswith("GIGACHAT_CREDENTIALS="):
                                new_lines.append(f"GIGACHAT_CREDENTIALS={auth_token}")
                            else:
                                new_lines.append(line)
                        with open(env_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(new_lines) + "\n")
                    else:
                        # Добавляем в конец
                        with open(env_path, "a", encoding="utf-8") as f:
                            f.write(f"\nGIGACHAT_CREDENTIALS={auth_token}\n")
                
                # Обновляем текущее окружение
                os.environ["GIGACHAT_CREDENTIALS"] = auth_token
                print("✅ Токен сохранен в .env и применен.")
            else:
                raise ValueError("Токен не введен.")
            
        # Для официальной библиотеки используется credentials
        kwargs = {"credentials": auth_token}

    chat = CustomGigaChat(
        base_url=base_url,
        verify_ssl_certs=False,
        model=model_name,
        temperature=temperature,
        **kwargs
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
