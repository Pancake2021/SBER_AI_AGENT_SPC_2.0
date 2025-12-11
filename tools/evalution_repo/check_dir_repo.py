"""Проверка структуры директорий репозитория"""


# Список корректных названий директорий
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


class EvalDir:
    """Класс для оценки структуры директорий репозитория"""

    def __init__(self):
        self.valid_dirs = DIRS

    def score_gitignore(self, files: list) -> int:
        """Проверить наличие .gitignore (0-1 балл)"""
        gitignore_files = [".gitignore", ".gitattributes"]
        for f in files:
            if any(f.endswith(g) for g in gitignore_files):
                return 1
        return 0

    def score_dirs_check(self, dirs: list) -> int:
        """Проверить корректность имён папок (0-2 балла)"""
        if not dirs:
            return 0
        
        valid_count = 0
        total = len(dirs)
        
        for d in dirs:
            d_lower = d.lower().replace("-", "_")
            # Проверяем соответствие стандартам
            if d_lower in self.valid_dirs or d.islower() or "_" in d:
                valid_count += 1
        
        ratio = valid_count / total if total > 0 else 0
        
        if ratio >= 0.8:
            return 2
        elif ratio >= 0.5:
            return 1
        return 0

    def score_files(self, files: list) -> int:
        """Проверить корректность имён файлов (0-2 балла)"""
        if not files:
            return 0
        
        valid_count = 0
        total = len(files)
        
        for f in files:
            name = f.split("/")[-1]
            # Файлы должны быть в snake_case или с допустимыми символами
            if (
                name.islower() or
                "_" in name or
                name.startswith(".") or
                name in ["README.md", "LICENSE", "Makefile", "Dockerfile"]
            ):
                valid_count += 1
        
        ratio = valid_count / total if total > 0 else 0
        
        if ratio >= 0.8:
            return 2
        elif ratio >= 0.5:
            return 1
        return 0

    def score_requirements(self, files: list) -> int:
        """Проверить наличие requirements.txt (0-2 балла)"""
        req_files = ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]
        
        score = 0
        for f in files:
            if any(f.endswith(r) for r in req_files):
                score += 1
                if score >= 2:
                    return 2
        return score

    def score_code_dirs(self, files: list, dirs: list) -> int:
        """Проверить наличие структуры для кода (0-2 балла)"""
        code_dirs = ["src", "source", "lib", "app", "core", "scripts"]
        
        # Проверяем наличие кода в корректных директориях
        has_code_dir = any(d.lower() in code_dirs for d in dirs)
        
        # Проверяем наличие __init__.py
        has_init = any(f.endswith("__init__.py") for f in files)
        
        score = 0
        if has_code_dir:
            score += 1
        if has_init:
            score += 1
        
        return score

    def get_score(self, files: list, dirs: list = None) -> dict:
        """Итоговая оценка структуры репозитория (0-9 баллов)"""
        if dirs is None:
            dirs = list(set(f.split("/")[0] for f in files if "/" in f))
        
        scores = {
            "gitignore": self.score_gitignore(files),       # 0-1
            "dirs_naming": self.score_dirs_check(dirs),      # 0-2
            "files_naming": self.score_files(files),          # 0-2
            "requirements": self.score_requirements(files),   # 0-2
            "code_structure": self.score_code_dirs(files, dirs)  # 0-2
        }
        
        total = sum(scores.values())
        
        return {
            "total": total,
            "max": 9,
            "details": scores,
            "comments": self._generate_comments(scores)
        }

    def _generate_comments(self, scores: dict) -> list:
        """Генерация комментариев по оценке"""
        comments = []
        
        if scores["gitignore"] == 0:
            comments.append("❌ Отсутствует .gitignore файл")
        else:
            comments.append("✅ .gitignore присутствует")
        
        if scores["dirs_naming"] < 2:
            comments.append("⚠️ Некоторые директории имеют нестандартные имена")
        else:
            comments.append("✅ Имена директорий соответствуют стандартам")
        
        if scores["files_naming"] < 2:
            comments.append("⚠️ Некоторые файлы имеют нестандартные имена")
        else:
            comments.append("✅ Имена файлов соответствуют стандартам")
        
        if scores["requirements"] == 0:
            comments.append("❌ Отсутствует requirements.txt или аналог")
        else:
            comments.append("✅ Файл зависимостей присутствует")
        
        if scores["code_structure"] < 2:
            comments.append("⚠️ Структура кода может быть улучшена")
        else:
            comments.append("✅ Хорошая структура кода")
        
        return comments
