"""
🎭 Сценарий: "Аудит Наследия"
============================

Этот скрипт демонстрирует полный цикл работы Agent SPC.
Мы симулируем действия нового Tech Lead'а (Алекса), который проводит аудит репозитория.

⚠️ ВНИМАНИЕ: Для работы сценария требуются корректные настройки в .env файле!
(BitBucket токен, доступы, GigaChat)
"""

import sys
import os
import time
from loguru import logger
from pathlib import Path

# Добавляем корневую директорию в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_agent

# Настройка красивого вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(step_num, title, description):
    print(f"\n{Colors.HEADER}=== ШАГ {step_num}: {title} ==={Colors.ENDC}")
    print(f"{Colors.CYAN}📝 Контекст:{Colors.ENDC} {description}")

def print_user_action(prompt):
    print(f"{Colors.BLUE}👤 Алекс пишет:{Colors.ENDC} {Colors.BOLD}\"{prompt}\"{Colors.ENDC}")
    print(f"{Colors.WARNING}🤖 Агент думает...{Colors.ENDC}")

def print_agent_response(response):
    print(f"\n{Colors.GREEN}✅ Ответ Агента:{Colors.ENDC}")
    print("-" * 50)
    print(response.text)
    print("-" * 50)
    if response.score:
        print(f"{Colors.CYAN}📊 Оценка:{Colors.ENDC} {response.score}")
    print(f"{Colors.CYAN}🔢 Токены:{Colors.ENDC} {response.tokens_used}")

def setup_environment():
    """Проверка и настройка окружения перед запуском"""
    print(f"{Colors.BOLD}🔧 Проверка окружения...{Colors.ENDC}")
    
    # Проверяем GigaChat токен
    token = os.environ.get("GIGACHAT_CREDENTIALS") or os.environ.get("GIGACHAT_API_KEY") or os.environ.get("JPY_API_TOKEN")
    
    if not token:
        print(f"{Colors.WARNING}⚠️  Токен GigaChat не найден!{Colors.ENDC}")
        print("Для работы демо-сценария необходим доступ к GigaChat API.")
        print("Получить ключ можно здесь: https://developers.sber.ru/studio/workspace")
        
        try:
            token = input(f"{Colors.GREEN}Введите ваш GIGACHAT_CREDENTIALS: {Colors.ENDC}").strip()
        except EOFError:
            print(f"{Colors.FAIL}❌ Невозможно запросить ввод (нет интерактивного терминала).{Colors.ENDC}")
            print("Пожалуйста, добавьте GIGACHAT_CREDENTIALS в файл .env вручную.")
            sys.exit(1)
            
        if token:
            # Сохраняем в .env
            env_path = Path(".env")
            if not env_path.exists():
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(f"GIGACHAT_CREDENTIALS={token}\n")
            else:
                with open(env_path, "a", encoding="utf-8") as f:
                    f.write(f"\nGIGACHAT_CREDENTIALS={token}\n")
            
            os.environ["GIGACHAT_CREDENTIALS"] = token
            print(f"{Colors.GREEN}✅ Токен сохранен и применен.{Colors.ENDC}\n")
        else:
            print(f"{Colors.FAIL}❌ Токен не введен. Запуск невозможен.{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"{Colors.GREEN}✅ GigaChat токен найден.{Colors.ENDC}\n")

    # Проверяем VCS (BitBucket или GitHub)
    bb_token = os.environ.get("TOKEN_BITBUCKET")
    gh_token = os.environ.get("GITHUB_TOKEN")
    
    if not bb_token and not gh_token:
        print(f"\n{Colors.WARNING}⚠️  Не найдены токены доступа к репозиториям (BitBucket/GitHub).{Colors.ENDC}")
        print("Мы можем использовать GitHub для теста.")
        print("Если у вас нет токена, можно попробовать работать с публичными репозиториями (но лучше с токеном).")
        
        choice = input("Хотите настроить GitHub? (y/n): ").strip().lower()
        if choice == 'y':
            gh_token = input("Введите GITHUB_TOKEN: ").strip()
            gh_owner = input("Введите GITHUB_OWNER (имя пользователя): ").strip()
            
            if gh_token and gh_owner:
                env_path = Path(".env")
                with open(env_path, "a", encoding="utf-8") as f:
                    f.write(f"\nGITHUB_TOKEN={gh_token}\n")
                    f.write(f"GITHUB_OWNER={gh_owner}\n")
                
                os.environ["GITHUB_TOKEN"] = gh_token
                os.environ["GITHUB_OWNER"] = gh_owner
                print(f"{Colors.GREEN}✅ GitHub настроен.{Colors.ENDC}\n")
            else:
                print("Пропуск настройки GitHub.")
        else:
            print("Пропуск настройки. Агент может не работать корректно без доступа к репозиторию.")

def run_scenario():
    # Имя репозитория для тестов
    # По умолчанию используем текущий проект, если он есть на GitHub
    default_repo = "SBER_AI_AGENT_SPC_2.0"
    REPO_NAME = os.getenv("GIT_NAME_PROJECT_BB") or default_repo
    
    # Если мы используем GitHub, имя проекта в env может не совпадать, спросим пользователя или используем дефолт
    if os.environ.get("GITHUB_TOKEN"):
        print(f"\n{Colors.CYAN}Используем GitHub режим.{Colors.ENDC}")
        user_repo = input(f"Введите имя репозитория для анализа (Enter для '{default_repo}'): ").strip()
        if user_repo:
            REPO_NAME = user_repo
    
    print(f"{Colors.BOLD}🚀 Запуск демонстрационного сценария 'Аудит Наследия'{Colors.ENDC}")
    print(f"Целевой репозиторий: {REPO_NAME}\n")

    # Сценарий
    steps = [
        {
            "title": "Знакомство",
            "desc": "Алекс только что установил агента и хочет узнать, что тот умеет.",
            "prompt": "Привет! Расскажи подробно, какие у тебя есть инструменты и что ты умеешь делать?"
        },
        {
            "title": "Поиск информации",
            "desc": "Алекс хочет узнать, как в компании принято оформлять коммиты или работать с БД.",
            "prompt": "Найди информацию о том, как правильно оформлять структуру проекта и какие есть стандарты кодирования."
        },
        {
            "title": "Разведка репозитория",
            "desc": "Алекс начинает изучать целевой репозиторий. Ему нужен список файлов.",
            "prompt": f"Покажи мне список всех файлов в репозитории {REPO_NAME}. Хочу понять его структуру."
        },
        {
            "title": "Анализ содержимого",
            "desc": "Алекс увидел интересный файл (например, requirements.txt или main.py) и хочет его прочитать.",
            "prompt": f"Прочитай файл requirements.txt в репозитории {REPO_NAME}. Хочу проверить зависимости."
        },
        {
            "title": "Оценка оформления",
            "desc": "Алекс хочет получить формальную оценку структуры проекта по стандартам компании.",
            "prompt": f"Проведи оценку оформления репозитория {REPO_NAME}. Проверь структуру папок и наличие документации."
        },
        {
            "title": "Code Review",
            "desc": "Самое важное: автоматический анализ качества кода линтерами.",
            "prompt": f"Оцени качество кода в репозитории {REPO_NAME}. Запусти линтеры для Python и SQL."
        },
        {
            "title": "Генерация документации",
            "desc": "Алекс заметил, что README устарел, и просит агента обновить его.",
            "prompt": f"Сгенерируй новый подробный README.md файл для репозитория {REPO_NAME} на основе его кода."
        }
    ]

    for i, step in enumerate(steps, 1):
        print_step(i, step["title"], step["desc"])
        print_user_action(step["prompt"])
        
        try:
            # Задержка для реалистичности
            time.sleep(1)
            
            # Вызов агента
            result = run_agent(step["prompt"])
            
            print_agent_response(result)
            
        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Ошибка выполнения шага:{Colors.ENDC} {e}")
            print("Проверьте настройки .env и доступность сервисов.")
            # Не прерываем сценарий, пробуем следующий шаг
            continue
        
        print("\nПереход к следующему шагу через 2 секунды...")
        time.sleep(2)

    print(f"\n{Colors.BOLD}🏁 Сценарий завершен!{Colors.ENDC}")
    print("Алекс получил полный отчет о проекте и сэкономил часы работы. 🎉")

if __name__ == "__main__":
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Настраиваем окружение
    setup_environment()
    
    run_scenario()
