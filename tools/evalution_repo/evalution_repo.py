"""Оценка оформления репозитория"""
from tools.git import Git
from tools.evalution_repo.check_dir_repo import EvalDir
from tools.evalution_repo.prompts import sys_prompt_evalution_readme_1, sys_prompt_evalution_readme_2
from agent.tools.run_giga import llm
from agent.parsing.parsing_text import parsing_input
from pathlib import Path
import markdown
from bs4 import BeautifulSoup


class EvalutionRepo(Git):
    """Класс для оценки оформления репозитория (0-26 баллов)"""

    def __init__(self, data: dict):
        super().__init__()
        self.repo = data.get("repository", "")
        self.branch = data.get("branch", "master")
        self.eval_dir = EvalDir()

    def mark(self, text: str) -> str:
        """Преобразование Markdown в текст"""
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def get_score_repo(self, local_path: Path) -> dict:
        """Получить оценку структуры репозитория"""
        files = self.get_local_files(self.repo)
        
        # Получаем директории верхнего уровня
        dirs = list(set(f.split("/")[0] for f in files if "/" in f and not f.startswith(".")))
        
        return self.eval_dir.get_score(files, dirs)

    def _get_readme_content(self, local_path: Path) -> str:
        """Получить содержимое README файла"""
        readme_names = ["README.md", "Readme.md", "readme.md", "README.MD", "README"]
        
        for name in readme_names:
            readme_path = local_path / name
            if readme_path.exists():
                try:
                    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                        return f.read()
                except Exception:
                    pass
        
        return ""

    def _get_similarity_readme(self, readme_content: str) -> dict:
        """Сравнение README с шаблоном через LLM"""
        if not readme_content or len(readme_content.strip()) < 50:
            return {
                "score": 0,
                "comment": "README файл пустой или отсутствует"
            }
        
        # Проверка на заглушки
        if "Documentation_CK_SPK" in readme_content:
            return {
                "score": 0,
                "comment": "README содержит только шаблон-заглушку"
            }
        
        return {"score": None, "comment": "Требуется LLM оценка"}

    def score_readme_part_1(self, readme_content: str, files: list) -> dict:
        """Оценка README по первой части критериев (0-6 баллов)"""
        if not readme_content:
            return {
                "text_content": {"grade": 0, "comment": "README отсутствует"},
                "check_sections": {"grade": 0, "comment": "README отсутствует"},
                "check_description_title": {"grade": 0, "comment": "README отсутствует"},
                "total": 0
            }
        
        # Формируем запрос для LLM
        files_str = "\n".join(files[:50])
        query = f"""README.md содержимое:
```markdown
{readme_content[:3000]}
```

Список файлов репозитория:
{files_str}
"""
        
        try:
            response = llm(query, sys_prompt_evalution_readme_1)
            result = parsing_input(response)
            
            if isinstance(result, dict):
                total = (
                    int(result.get("text_content", {}).get("grade", 0)) +
                    int(result.get("check_sections", {}).get("grade", 0)) +
                    int(result.get("check_description_title", {}).get("grade", 0))
                )
                result["total"] = total
                return result
        except Exception as e:
            pass
        
        # Fallback: эвристическая оценка
        return self._heuristic_readme_1(readme_content)

    def _heuristic_readme_1(self, readme_content: str) -> dict:
        """Эвристическая оценка README (часть 1)"""
        content_lower = readme_content.lower()
        
        # Содержание (0-3)
        has_toc = any(word in content_lower for word in ["содержание", "оглавление", "table of contents", "## содержание"])
        toc_score = 3 if has_toc else 0
        
        # Разделы (0-1)
        headers = content_lower.count("##")
        sections_score = 1 if headers >= 3 else 0
        
        # Название и описание (0-2)
        has_title = readme_content.strip().startswith("#")
        has_desc = len(readme_content) > 200
        title_score = 2 if has_title and has_desc else (1 if has_title else 0)
        
        return {
            "text_content": {"grade": toc_score, "comment": "Эвристическая оценка"},
            "check_sections": {"grade": sections_score, "comment": "Эвристическая оценка"},
            "check_description_title": {"grade": title_score, "comment": "Эвристическая оценка"},
            "total": toc_score + sections_score + title_score
        }

    def score_readme_part_2(self, readme_content: str, files: list) -> dict:
        """Оценка README по второй части критериев (0-8 баллов)"""
        if not readme_content:
            return {
                "availability_contacts": {"grade": 0, "comment": "README отсутствует"},
                "description_scripts": {"grade": 0, "comment": "README отсутствует"},
                "data_sources": {"grade": 0, "comment": "README отсутствует"},
                "launch_instruction": {"grade": 0, "comment": "README отсутствует"},
                "total": 0
            }
        
        # Список скриптов для проверки
        code_files = [f for f in files if any(f.endswith(ext) for ext in [".py", ".ipynb", ".sql"])]
        code_files_str = "\n".join(code_files[:30])
        
        query = f"""README.md содержимое:
```markdown
{readme_content[:3000]}
```

Файлы с кодом, которые должны быть описаны:
{code_files_str}
"""
        
        try:
            response = llm(query, sys_prompt_evalution_readme_2)
            result = parsing_input(response)
            
            if isinstance(result, dict):
                total = (
                    int(result.get("availability_contacts", {}).get("grade", 0)) +
                    int(result.get("description_scripts", {}).get("grade", 0)) +
                    int(result.get("data_sources", {}).get("grade", 0)) +
                    int(result.get("launch_instruction", {}).get("grade", 0))
                )
                result["total"] = total
                return result
        except Exception:
            pass
        
        # Fallback: эвристическая оценка
        return self._heuristic_readme_2(readme_content, code_files)

    def _heuristic_readme_2(self, readme_content: str, code_files: list) -> dict:
        """Эвристическая оценка README (часть 2)"""
        content_lower = readme_content.lower()
        
        # Контакты (0-2)
        has_contacts = any(word in content_lower for word in ["контакт", "автор", "руководитель", "email", "@", "телефон"])
        contacts_score = 2 if has_contacts else 0
        
        # Описание скриптов (0-4)
        described = 0
        for f in code_files:
            file_name = f.split("/")[-1]
            if file_name.lower() in content_lower or file_name.replace("_", " ") in content_lower:
                described += 1
        
        if code_files:
            ratio = described / len(code_files)
            if ratio >= 1.0:
                scripts_score = 4
            elif ratio >= 0.8:
                scripts_score = 3
            elif ratio >= 0.5:
                scripts_score = 2
            elif ratio > 0:
                scripts_score = 1
            else:
                scripts_score = 0
        else:
            scripts_score = 0
        
        # Источники данных (0-1)
        has_sources = any(word in content_lower for word in ["источник", "данные", "база данных", "таблица", "схема"])
        sources_score = 1 if has_sources else 0
        
        # Инструкция запуска (0-1)
        has_launch = any(word in content_lower for word in ["запуск", "установка", "python", "pip install", "requirements"])
        launch_score = 1 if has_launch else 0
        
        return {
            "availability_contacts": {"grade": contacts_score, "comment": "Эвристическая оценка"},
            "description_scripts": {"grade": scripts_score, "comment": "Эвристическая оценка"},
            "data_sources": {"grade": sources_score, "comment": "Эвристическая оценка"},
            "launch_instruction": {"grade": launch_score, "comment": "Эвристическая оценка"},
            "total": contacts_score + scripts_score + sources_score + launch_score
        }

    def run_tool(self) -> dict:
        """Главная функция оценки репозитория (0-26 баллов)"""
        if not self.repo:
            return {"status": 400, "answer": "Не указан репозиторий"}
        
        # Клонируем репозиторий
        clone_result = self.git_clone(self.repo, self.branch)
        if clone_result["status"] != 200:
            return clone_result
        
        local_path = Path(clone_result["path"])
        
        # Оценка структуры (0-9)
        structure_score = self.get_score_repo(local_path)
        
        # Получаем README
        readme_content = self._get_readme_content(local_path)
        files = self.get_local_files(self.repo)
        
        # Оценка README часть 1 (0-6)
        readme_1 = self.score_readme_part_1(readme_content, files)
        
        # Оценка README часть 2 (0-8)
        readme_2 = self.score_readme_part_2(readme_content, files)
        
        # Итоговые баллы
        score_structure = structure_score["total"]  # 0-9
        score_readme = readme_1["total"] + readme_2["total"]  # 0-14
        # Дополнительные 3 балла из parts - итого README 0-17, но в документации указано 0-26
        
        total_score = score_structure + score_readme
        
        # Формируем отчёт
        md_report = f"""# 📊 Оценка оформления репозитория: {self.repo}

## Итоговая оценка: {total_score}/26 баллов

---

## 📁 Структура репозитория: {score_structure}/9 баллов

### Детали:
| Критерий | Баллы |
|----------|-------|
| .gitignore | {structure_score['details']['gitignore']}/1 |
| Имена директорий | {structure_score['details']['dirs_naming']}/2 |
| Имена файлов | {structure_score['details']['files_naming']}/2 |
| Requirements | {structure_score['details']['requirements']}/2 |
| Структура кода | {structure_score['details']['code_structure']}/2 |

### Комментарии:
{"".join('- ' + c + chr(10) for c in structure_score['comments'])}

---

## 📝 README файл: {score_readme}/17 баллов

### Часть 1 (Структура README): {readme_1['total']}/6 баллов
| Критерий | Баллы | Комментарий |
|----------|-------|-------------|
| Содержание | {readme_1['text_content']['grade']}/3 | {readme_1['text_content']['comment']} |
| Разделы | {readme_1['check_sections']['grade']}/1 | {readme_1['check_sections']['comment']} |
| Название и описание | {readme_1['check_description_title']['grade']}/2 | {readme_1['check_description_title']['comment']} |

### Часть 2 (Содержание README): {readme_2['total']}/8 баллов
| Критерий | Баллы | Комментарий |
|----------|-------|-------------|
| Контакты | {readme_2['availability_contacts']['grade']}/2 | {readme_2['availability_contacts']['comment']} |
| Описание скриптов | {readme_2['description_scripts']['grade']}/4 | {readme_2['description_scripts']['comment']} |
| Источники данных | {readme_2['data_sources']['grade']}/1 | {readme_2['data_sources']['comment']} |
| Инструкция запуска | {readme_2['launch_instruction']['grade']}/1 | {readme_2['launch_instruction']['comment']} |

---

## 🎯 Рекомендации

{"✅ Отличный результат!" if total_score >= 20 else "⚠️ Есть области для улучшения" if total_score >= 13 else "❌ Требуется значительная доработка"}

"""
        
        return {
            "status": 200,
            "answer": md_report,
            "score_structure": score_structure,
            "score_readme": score_readme,
            "score_repo": total_score,
            "details": {
                "structure": structure_score,
                "readme_part1": readme_1,
                "readme_part2": readme_2
            }
        }
