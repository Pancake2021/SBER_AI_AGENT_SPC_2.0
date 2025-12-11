"""Менеджер инструментов агента"""
import requests
from loguru import logger


TOOLS_DESCRIPTION = """
Доступные инструменты:

1. **search_content** - Семантический поиск по базе знаний
   - Параметры: {"name_tool": "search_content", "query": "поисковый запрос"}
   - Использует BGEM3FlagModel для векторного поиска

2. **read_file** - Чтение файла из репозитория BitBucket
   - Параметры: {"name_tool": "read_file", "repository": "имя_репо", "file_path": "путь/к/файлу"}

3. **show_files** - Показать список файлов репозитория
   - Параметры: {"name_tool": "show_files", "repository": "имя_репо"}

4. **gen_readme** - Генерация README.md для репозитория
   - Параметры: {"name_tool": "gen_readme", "repository": "имя_репо"}

5. **awerage_repo** - Оценка оформления репозитория (0-26 баллов)
   - Параметры: {"name_tool": "awerage_repo", "repository": "имя_репо"}
   - Проверяет структуру и README

6. **rate_repository** - Оценка качества кода (Python/Jupyter/SQL)
   - Параметры: {"name_tool": "rate_repository", "repository": "имя_репо"}
   - Использует pylint, nbqa, sqlfluff

7. **info_tools** - Информация о возможностях агента
   - Параметры: {"name_tool": "info_tools"}

8. **answer** - Завершить выполнение и вернуть ответ
   - Параметры: {"name_tool": "answer"}
"""


def get_tools(data: dict) -> dict:
    """Получить список доступных инструментов"""
    return {"list_tools": TOOLS_DESCRIPTION}


def run_tools(content: dict, api_url: str = "http://localhost:5001") -> dict:
    """
    Выполнить инструмент через HTTP запрос к Flask API
    
    Args:
        content: Словарь с параметрами инструмента
        api_url: URL Flask API сервера
    
    Returns:
        Результат выполнения инструмента
    """
    name_tool = content.get("name_tool")
    
    if not name_tool:
        return {"status": 400, "answer": "Не указан инструмент (name_tool)"}
    
    # Маппинг инструментов на endpoints
    endpoints = {
        "search_content": "/search_content",
        "read_file": "/read_file",
        "show_files": "/show_files",
        "gen_readme": "/gen_readme",
        "awerage_repo": "/awerage_repo",
        "rate_repository": "/rate_repository",
        "info_tools": "/info_tools",
    }
    
    endpoint = endpoints.get(name_tool)
    
    if not endpoint:
        logger.warning(f"Неизвестный инструмент: {name_tool}")
        return {"status": 404, "answer": f"Инструмент не найден: {name_tool}"}
    
    try:
        response = requests.post(
            f"{api_url}{endpoint}",
            json=content,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": response.status_code, "answer": f"Ошибка API: {response.text}"}
    except requests.exceptions.ConnectionError:
        logger.warning(f"Flask API не запущен ({api_url}), используем локальное выполнение")
        # Fallback: локальное выполнение
        return run_tools_local(content)
    except Exception as e:
        logger.error(f"Ошибка выполнения инструмента: {str(e)}")
        return {"status": 500, "answer": f"Ошибка: {str(e)}"}


def run_tools_local(content: dict) -> dict:
    """Локальное выполнение инструментов (без HTTP)"""
    name_tool = content.get("name_tool")
    
    try:
        if name_tool == "search_content":
            from tools.search_content import Search
            search = Search()
            result = search.run_tool(content.get("query", ""))
        
        elif name_tool == "read_file":
            from tools.bitbucket import ConnectionAPI
            api = ConnectionAPI()
            result = api.read_file_bb(content)
        
        elif name_tool == "show_files":
            from tools.bitbucket import ConnectionAPI
            api = ConnectionAPI()
            result = api.get_files(content.get("repository", ""))
        
        elif name_tool == "gen_readme":
            from tools.gen_main import GenReadme
            gen = GenReadme(content)
            result = gen.run_tool()
        
        elif name_tool == "awerage_repo":
            from tools.evalution_repo.evalution_repo import EvalutionRepo
            ev = EvalutionRepo(content)
            result = ev.run_tool()
        
        elif name_tool == "rate_repository":
            from tools.evalution_code.awerage_main import EvalutionCode
            ev = EvalutionCode(content)
            result = ev.run_tool()
        
        elif name_tool == "info_tools":
            from tools.info_tool import InfoTools
            info = InfoTools()
            result = info.result()
        
        else:
            return {"status": 404, "answer": f"Инструмент не найден: {name_tool}"}
        
        logger.info(f"Инструмент {name_tool} выполнен успешно (локально)")
        return result
    
    except Exception as e:
        logger.error(f"Ошибка локального выполнения: {str(e)}")
        return {"status": 500, "answer": f"Ошибка: {str(e)}"}

