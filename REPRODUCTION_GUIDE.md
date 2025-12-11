"""
ПОЛНЫЙ СПИСОК ФАЙЛОВ ДЛЯ ВОСПРОИЗВЕДЕНИЯ ПРОЕКТА DSC 18 (Agent SPC)

Я создал полную структуру. Вот что нужно дополнить вручную:
"""

# ============================================================================
# ГОТОВЫЕ ФАЙЛЫ (созданы выше)
# ============================================================================

FILES_CREATED = {
    # Schemas
    "schemas/answer.py": "Answer - Pydantic модель для ответов",
    
    # Exceptions
    "agent/tools/exceptions.py": "GigaChatException, BlackList, CustomError",
    
    # LLM
    "agent/tools/run_giga.py": "CustomGigaChat, llm(), write_tokens()",
    
    # Memory & State
    "agent/memory/memory_state.py": "State, AgentState, should_continue()",
    "agent/memory/get_prompts.py": "get_history_prompt(), final_answer()",
    
    # Parsing
    "agent/parsing/parsing_text.py": "parsing_input(), parsing_html()",
    "agent/parsing/parsing_llm.py": "ParseLLM, classification_query()",
    "agent/parsing/parsing_state.py": "post_form_instrument()",
    
    # Prompts
    "agent/prompts/prompts.py": "Все системные промпты",
    
    # Main Agent
    "agent/main_structure.py": "main_agent()",
    "agent/state_graph/graph.py": "StateGraph, agent()",
    
    # Configuration
    "tools/settings.py": "Configure - загрузка конфигурации",
}

# ============================================================================
# ФАЙЛЫ, КОТОРЫЕ НУЖНО СОЗДАТЬ (код из оригинального проекта)
# ============================================================================

REMAINING_FILES = {
    # Tools - BitBucket & Git
    "tools/bitbucket.py": """
ConnectionAPI класс с методами:
- get_requests() - GET запросы
- read_file_bb() - чтение файла
- get_files() - список файлов
- get_files_repo_awerage() - проверка наличия кода
- get_description_repo() - описание репо
- get_repos_list() - список репо
- get_commits() - коммиты
- _get_main_user() - изменения по юзерам
- get_login_user() - логин по ФИО
- get_users_permission() - права доступа
""",
    
    "tools/git.py": """
Git класс (наследует ConnectionAPI) с методами:
- git_clone(repo, branch='') - клонирование
- ensure_branch_and_update() - переключение веток
- _dell_repo() - удаление локального репо
""",
    
    # Tools - Search
    "tools/search_content.py": """
Search класс с методами:
- __init__(top_k=7) - инициализация BGEM3FlagModel
- get_vecs_bge() - получение векторов
- get_texts() - загрузка текстов из data_cards
- run_tool(quest) - семантический поиск
- answer_llm() - генерация ответа
- score_answer() - оценка ответа
Возвращает: {status, answer, relevant_doc, chunks, score}
""",
    
    # Tools - README Generation
    "tools/gen_main.py": """
GenReadme класс с методом:
- run_tool() - генерация README файла
Возвращает: {status, answer}
""",
    
    # Tools - Info
    "tools/info_tool.py": """
InfoTools класс с методом:
- result() - описание всех возможностей агента
""",
    
    # Tools - Main tools.py
    "tools/tools.py": """
Функции:
- get_tools() - получить список доступных инструментов
- run_tools(content) - HTTP запрос к Flask API
""",
    
    # Evaluation Code
    "tools/evalution_code/awerage_py_files.py": """
Функции:
- awerage_py(repo) - найти .py файлы
- run_pylint(py_files) - запустить pylint
- parse_file_pylint() - парсить результаты
- main_awerage_py(repo) - главная функция
""",
    
    "tools/evalution_code/awerage_ipynb_files.py": """
Функции:
- awerage_ipynb(repo) - найти .ipynb файлы
- run_nbqa(ipynb_files) - запустить nbqa
- parse_file_nbqa() - парсить результаты
- main_awerage_ipynb(repo) - главная функция
""",
    
    "tools/evalution_code/awerage_sql_files.py": """
Функции:
- awerage_sql(repo) - найти .sql файлы
- get_dialect(context) - определить диалект
- run_sqlfluff() - запустить sqlfluff
- main_awerage_sql(repo) - главная функция
""",
    
    "tools/evalution_code/awerage_main.py": """
EvalutionCode класс (наследует Git) с методами:
- get_score_repo() - получить оценку структуры
- run_tool() - главная функция оценки кода
Возвращает оценку: Python (0-10), Jupyter (0-10), SQL (OK/ERRORS)
""",
    
    # Evaluation Repo
    "tools/evalution_repo/check_dir_repo.py": """
EvalDir класс с методами:
- score_gitignore() - проверить .gitignore
- score_dirs_check() - проверить имена папок
- score_files() - проверить имена файлов
- score_requirements() - проверить requirements.txt
- score_code_dirs() - проверить структуру кода
- get_score(files) - итоговая оценка структуры (0-9)
""",
    
    "tools/evalution_repo/evalution_repo.py": """
EvalutionRepo класс (наследует Git) с методом:
- run_tool() - оценка README и структуры репо
Возвращает: {status, answer, score_structure, score_readme, score_repo}
Итоговая оценка: 0-26 баллов
""",
    
    "tools/evalution_repo/prompts.py": """
sys_prompt_evalution_readme_1 - первый критерий оценки README
sys_prompt_evalution_readme_2 - второй критерий оценки README
""",
    
    "tools/evalution_repo/settings.py": """
TB = [] - список аббревиатур тер. банков
DIRS = [] - список корректных директорий
""",
    
    # Entry points
    "main.py": """
run_agent(task) - главная функция
1. classification_query() - проверка релевантности
2. agent() - StateGraph.invoke()
3. Возврат Answer(text, relevant_docs, context, score, tokens)
""",
    
    "git_clone_free.py": """
RunningTheScript класс для автоаутентификации:
- create_git_files() - создание .gitconfig и .git-credentials
- _check_password() - проверка пароля
- git() - главная функция
""",
    
    "run_mlflow_server.py": """
Flask приложение с endpoints:
- GET /show_tools - список инструментов
- POST /search_content - поиск контента
- POST /read_file - чтение файла
- POST /show_files - список файлов
- POST /rate_repository - оценка кода
- POST /gen_readme - генерация README
- POST /awerage_repo - оценка оформления
- POST /info_tools - информация

+ MLflow UI на порту 5000
""",
    
    # Config files
    ".env": """
TOKEN_BITBUCKET=<ваш_токен>
LOGIN=<логин>
PSW=<пароль>
GIT_NAME_PROJECT_BB=SVA_CODE (или указать пользователя)
GIT_NAME_USER_BB=<номер_пользователя>

PATH_MODEL_M3=/path/to/BGEM3FlagModel
PATH_PICKLE_FILE=/home/datalab/vect_bge.pkl
PATH_BASE_CARD=/home/datalab/
PATH_FILE=output/readme_test/
PATH_CLONE=output/clone_repo/
PYLINTRC=tools/evalution_code/config/pylintrc
PYLINTRC_IPYNB=tools/evalution_code/config/pylintrc_ipynb
TOX=tools/evalution_code/config/tox.ini
PATH_ERRORS_FILE=tools/evalution_code/errors/
""",
    
    ".gitignore": """
.ipynb_checkpoints/
__pycache__/
.idea/
*.egg-info/
venv/
env/
*.pyc
.DS_Store
output/
.env.local
""",
    
    "requirements.txt": """
langgraph==0.4.7
langchain-community
python-dotenv==1.0.1
pylint==3.0.0
nbqa==1.8.4
sqlfluff==3.1.1
chardet==5.2.0
FlagEmbedding
flask
mlflow
pydantic
beautifulsoup4
markdown
gitpython
requests
loguru
""",
    
    # Tests
    "tests.ipynb": """
Jupyter notebook с примерами:
- BitBucket API operations
- Git operations
- GenReadme
- Search content
- EvalutionRepo
- EvalutionCode
- Classification query
- GigaChat API
""",
    
    # Documentation
    "README.md": """
Основная документация проекта с описанием возможностей
""",
    
    "readme_agent.md": """
Описание агента и его возможностей
""",
}

# ============================================================================
# ДИРЕКТОРИИ, КОТОРЫЕ НУЖНО СОЗДАТЬ
# ============================================================================

DIRECTORIES = [
    "agent/",
    "agent/memory/",
    "agent/parsing/",
    "agent/prompts/",
    "agent/state_graph/",
    "agent/tools/",
    "tools/",
    "tools/evalution_code/",
    "tools/evalution_code/config/",
    "tools/evalution_code/errors/",
    "tools/evalution_repo/",
    "schemas/",
    "output/",
    "output/readme_test/",
    "output/clone_repo/",
]

# ============================================================================
# __init__.py ФАЙЛЫ
# ============================================================================

INIT_FILES = [
    "agent/__init__.py",
    "agent/memory/__init__.py",
    "agent/parsing/__init__.py",
    "agent/prompts/__init__.py",
    "agent/state_graph/__init__.py",
    "agent/tools/__init__.py",
    "tools/__init__.py",
    "tools/evalution_code/__init__.py",
    "tools/evalution_repo/__init__.py",
    "schemas/__init__.py",
]

# ============================================================================
# ИНСТРУКЦИЯ ПО ВОСПРОИЗВЕДЕНИЮ
# ============================================================================

REPRODUCTION_STEPS = """
1. Создать директории из DIRECTORIES

2. Создать все __init__.py файлы (могут быть пусты)

3. Скопировать созданные файлы в соответствующие директории

4. Создать файлы config (pylintrc, pylintrc_ipynb, tox.ini) в 
   tools/evalution_code/config/
   (Можно скопировать из оригинального проекта или использовать 
    стандартные конфиги pylint и sqlfluff)

5. Создать .env файл с необходимыми переменными окружения

6. Установить зависимости:
   pip install -r requirements.txt

7. Добавить файлы из REMAINING_FILES с кодом из оригинального проекта

8. Запустить агент:
   python main.py

9. Или запустить Flask сервер:
   python run_mlflow_server.py

10. Для тестирования использовать tests.ipynb в JupyterHub
"""

print(__doc__)
print("\n".join([f"✅ {f}" for f in FILES_CREATED.keys()]))
print("\nОстановка файлов для создания:")
print("\n".join([f"⏳ {f}" for f in REMAINING_FILES.keys()]))
