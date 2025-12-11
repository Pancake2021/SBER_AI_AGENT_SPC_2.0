# DSC 18 (Agent SPC) - Полная Структура Проекта

## 📁 Иерархия каталогов

```
DSC_18_Agent_SPC/
│
├── agent/                          # Ядро агента
│   ├── __init__.py
│   ├── main_structure.py            # Главная функция агента
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── memory_state.py          # State, AgentState, should_continue
│   │   └── get_prompts.py           # get_history_prompt(), final_answer()
│   ├── parsing/
│   │   ├── __init__.py
│   │   ├── parsing_llm.py           # ParseLLM, classification_query()
│   │   ├── parsing_state.py         # post_form_instrument()
│   │   └── parsing_text.py          # parsing_input(), parsing_html()
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── prompts.py               # Все системные промпты
│   ├── state_graph/
│   │   ├── __init__.py
│   │   └── graph.py                 # StateGraph, agent()
│   └── tools/
│       ├── __init__.py
│       ├── exceptions.py             # GigaChatException, BlackList, CustomError
│       └── run_giga.py              # CustomGigaChat, llm()
│
├── tools/                           # Инструменты
│   ├── __init__.py
│   ├── bitbucket.py                 # ConnectionAPI
│   ├── git.py                       # Git
│   ├── search_content.py            # Search
│   ├── gen_main.py                  # GenReadme
│   ├── info_tool.py                 # InfoTools
│   ├── settings.py                  # Configure
│   ├── tools.py                     # run_tools()
│   ├── evalution_code/
│   │   ├── __init__.py
│   │   ├── awerage_py_files.py      # main_awerage_py()
│   │   ├── awerage_ipynb_files.py   # main_awerage_ipynb()
│   │   ├── awerage_sql_files.py     # main_awerage_sql()
│   │   ├── awerage_main.py          # EvalutionCode
│   │   ├── config/
│   │   │   ├── pylintrc
│   │   │   ├── pylintrc_ipynb
│   │   │   └── tox.ini
│   │   └── errors/                  # Директория для результатов
│   └── evalution_repo/
│       ├── __init__.py
│       ├── check_dir_repo.py        # EvalDir
│       ├── evalution_repo.py        # EvalutionRepo
│       ├── prompts.py               # sys_prompt_evalution_readme_1/2
│       └── settings.py              # TB, DIRS
│
├── schemas/                         # Модели данных
│   ├── __init__.py
│   └── answer.py                    # Answer (Pydantic)
│
├── main.py                          # Точка входа (run_agent)
├── git_clone_free.py                # Автоаутентификация
├── run_mlflow_server.py             # Flask API сервер
├── tests.ipynb                      # Примеры использования
│
├── .env                             # Переменные окружения
├── .gitignore                       # Git исключения
├── requirements.txt                 # Зависимости
├── README.md                        # Основная документация
└── readme_agent.md                  # Описание агента
```

## 📦 Логические модули

### 1. **Agent Core** (agent/)
   - Граф состояний
   - Управление памятью
   - Парсинг запросов
   - Системные промпты
   - Взаимодействие с LLM

### 2. **Tools** (tools/)
   - BitBucket API
   - Git операции
   - Поиск контента (векторный)
   - Генерация README
   - Оценка кода (Python/Jupyter/SQL)
   - Оценка структуры репо

### 3. **Data Models** (schemas/)
   - Pydantic модели
   - Схемы ответов

### 4. **API & Entry Points**
   - Flask сервер (run_mlflow_server.py)
   - Главная функция (main.py)
   - Git аутентификация (git_clone_free.py)

### 5. **Tests & Documentation**
   - Jupyter примеры (tests.ipynb)
   - README файлы

## 🔑 Ключевые зависимости

```
langgraph==0.4.7            # Граф состояний
langchain-community         # LLM интеграции
gigachat                    # API GigaChat
python-dotenv==1.0.1        # .env конфиг
pylint==3.0.0               # Оценка Python
nbqa==1.8.4                 # Оценка Jupyter
sqlfluff==3.1.1             # Оценка SQL
chardet==5.2.0              # Определение кодировки
FlagEmbedding               # BGEM3FlagModel
flask                       # Web API
mlflow                      # Tracking
pydantic                    # Data validation
beautifulsoup4              # HTML парсинг
markdown                    # Markdown конверсия
gitpython                   # Git операции
requests                    # HTTP запросы
loguru                      # Логирование
```

## 🎯 Flow агента

```
run_agent(task)
    ↓
classification_query() - проверка релевантности
    ↓
agent(query) - StateGraph.invoke()
    ├─ show_tools() - получить список инструментов
    ├─ run_tool() - main_agent()
    │   ├─ get_history_prompt() - сформировать prompt
    │   ├─ ParseLLM.get_main_answer_agent() - получить action
    │   ├─ run_tools() - выполнить инструмент
    │   ├─ post_form_instrument() - обработать результат
    │   ├─ count_add() - увеличить счётчик
    │   └─ should_continue() - проверить условие выхода
    └─ final_answer() - генерировать финальный ответ
        ↓
Answer(text, relevant_docs, context, score, tokens)
```

## 📊 Инструменты

| Инструмент | Класс/Функция | Возвращает | Назначение |
|-----------|---------------|-----------|-----------|
| search_content | Search.run_tool() | dict | Семантический поиск |
| read_file | ConnectionAPI.read_file_bb() | str | Чтение файла |
| show_files | ConnectionAPI.get_files() | list | Список файлов |
| gen_readme | GenReadme.run_tool() | dict | Генерация README |
| awerage_repo | EvalutionRepo.run_tool() | dict | Оценка репо (0-26) |
| rate_repository | EvalutionCode.run_tool() | dict | Оценка кода |
| info_tools | InfoTools.result() | dict | Информация |

## 🔐 Конфигурация

Все параметры в `.env`:
- `TOKEN_BITBUCKET` - токен BitBucket
- `LOGIN` / `PSW` - учётные данные
- `PATH_MODEL_M3` - путь к BGEM3FlagModel
- `PATH_CLONE` - директория для клонирования
- `PATH_ERRORS_FILE` - директория для ошибок
- И другие...
