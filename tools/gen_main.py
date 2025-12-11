"""Генерация README для репозитория"""
from tools.git import Git
from agent.tools.run_giga import llm
from pathlib import Path


class GenReadme(Git):
    """Класс для генерации README.md файла"""

    def __init__(self, data: dict):
        super().__init__()
        self.repo = data.get("repository", "")
        self.branch = data.get("branch", "master")

    def _get_file_structure(self, local_path: Path) -> str:
        """Получить структуру файлов репозитория"""
        structure = []
        
        for item in sorted(local_path.rglob("*")):
            if ".git" in str(item):
                continue
            
            rel_path = item.relative_to(local_path)
            depth = len(rel_path.parts) - 1
            indent = "  " * depth
            
            if item.is_dir():
                structure.append(f"{indent}📁 {item.name}/")
            else:
                structure.append(f"{indent}📄 {item.name}")
        
        return "\n".join(structure[:100])  # Ограничение

    def _get_code_summary(self, local_path: Path) -> str:
        """Получить краткое содержание кода"""
        code_files = []
        
        for ext in ["*.py", "*.ipynb", "*.sql"]:
            for file_path in local_path.glob(f"**/{ext}"):
                if ".git" in str(file_path):
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()[:500]
                        code_files.append({
                            "file": file_path.name,
                            "preview": content
                        })
                except Exception:
                    continue
        
        summary = []
        for cf in code_files[:10]:
            summary.append(f"**{cf['file']}**:\n```\n{cf['preview'][:200]}...\n```")
        
        return "\n\n".join(summary)

    def run_tool(self) -> dict:
        """Генерация README.md для репозитория"""
        if not self.repo:
            return {"status": 400, "answer": "Не указан репозиторий"}
        
        # Клонируем репозиторий
        clone_result = self.git_clone(self.repo, self.branch)
        if clone_result["status"] != 200:
            return clone_result
        
        local_path = Path(clone_result["path"])
        
        # Собираем информацию
        file_structure = self._get_file_structure(local_path)
        code_summary = self._get_code_summary(local_path)
        
        # Получаем описание репо
        repo_info = self.get_description_repo(self.repo)
        repo_desc = repo_info.get("answer", {}).get("description", "") if repo_info["status"] == 200 else ""
        
        # Промпт для генерации README
        prompt = f"""Ты помощник для генерации README.md файлов.

Создай профессиональный README.md для репозитория на русском языке.

**Информация о репозитории:**
- Название: {self.repo}
- Описание: {repo_desc}

**Структура файлов:**
{file_structure}

**Примеры кода:**
{code_summary}

**Требования к README:**
1. Название и описание проекта
2. Содержание (оглавление)
3. Описание структуры проекта
4. Описание скриптов (.py, .ipynb, .sql)
5. Инструкция по установке и запуску
6. Контакты (выделить красным для заполнения)
7. Источники данных (если есть SQL)

Используй Markdown форматирование.
Места для заполнения пользователем выдели так: <span style="color:red">ЗАПОЛНИТЬ</span>
"""
        
        try:
            readme_content = llm(
                "Сгенерируй README.md файл для репозитория",
                prompt
            )
            
            # Сохраняем README
            output_path = Path(self.gen_readme_path) / f"{self.repo}_README.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            return {
                "status": 200,
                "answer": readme_content,
                "file_path": str(output_path)
            }
        
        except Exception as e:
            return {"status": 500, "answer": f"Ошибка генерации: {str(e)}"}
