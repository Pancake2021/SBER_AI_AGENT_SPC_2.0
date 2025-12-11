"""Настройки для оценки репозитория"""

# Список аббревиатур территориальных банков
TB = [
    "МОСБ", "МОБН", "СЗБ", "ЦЧБ", "ПСБ",
    "ЮЗБ", "УРБ", "СИБ", "ДВБ", "БВБ",
    "ССБ", "СРБ", "СКБ", "ЯРБ", "КРБ"
]

# Список корректных директорий проекта
DIRS = [
    "src", "source", "sources",
    "lib", "libs", "library",
    "test", "tests", "testing",
    "doc", "docs", "documentation",
    "data", "datasets",
    "config", "configs", "configuration",
    "scripts", "script",
    "notebooks", "notebook",
    "models", "model",
    "utils", "utilities", "helpers",
    "sql", "queries",
    "output", "outputs", "results",
    "logs", "log",
    "resources", "res",
    "assets", "static",
    "templates", "template",
    "migrations",
    "core", "app", "application"
]

# Обязательные секции README
README_SECTIONS = [
    "содержание",
    "описание",
    "установка",
    "использование",
    "контакты",
    "структура"
]

# Расширения кода
CODE_EXTENSIONS = [".py", ".ipynb", ".sql"]
