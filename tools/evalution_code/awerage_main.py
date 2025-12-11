"""Главный модуль оценки качества кода"""
from tools.git import Git
from tools.evalution_code.awerage_py_files import main_awerage_py
from tools.evalution_code.awerage_ipynb_files import main_awerage_ipynb
from tools.evalution_code.awerage_sql_files import main_awerage_sql
from pathlib import Path
import shutil


class EvalutionCode(Git):
    """Класс для оценки качества кода репозитория"""

    def __init__(self, data: dict):
        super().__init__()
        self.repo = data.get("repository", "")
        self.branch = data.get("branch", "master")
        self.text_only = data.get("text_only", False)

    def write_file_md(self, name: str, new_name: str, content: str) -> str:
        """Записать результаты оценки в MD файл"""
        output_path = Path(self.path_lint) / f"{new_name}_{name}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(output_path)

    def copy_files_lint(self, status: str):
        """Копирование файлов с ошибками в директорию errors"""
        pass  # Опциональная функциональность

    def _format_py_result(self, result: dict) -> str:
        """Форматировать результаты Python в Markdown"""
        if result["status"] == "NO_FILES":
            return "### Python (.py)\n\n❌ Python файлы не найдены\n"
        
        if result["status"] == "ERROR":
            return f"### Python (.py)\n\n⚠️ Ошибка: {result['message']}\n"
        
        md = f"""### Python (.py)

**Файлов:** {result['files_count']}  
**Оценка pylint:** {result['score']}/10  
**Всего проблем:** {result['total_issues']}

#### Разбивка по типам:
| Тип | Количество |
|-----|------------|
| ❌ Error | {result['errors']['error']} |
| ⚠️ Warning | {result['errors']['warning']} |
| 📝 Convention | {result['errors']['convention']} |
| 🔄 Refactor | {result['errors']['refactor']} |

"""
        if result.get("top_messages"):
            md += "#### Топ проблем:\n"
            for msg in result["top_messages"][:5]:
                md += f"- `{msg['code']}`: {msg['message']}\n"
        
        return md

    def _format_ipynb_result(self, result: dict) -> str:
        """Форматировать результаты Jupyter в Markdown"""
        if result["status"] == "NO_FILES":
            return "### Jupyter Notebook (.ipynb)\n\n❌ Jupyter файлы не найдены\n"
        
        if result["status"] == "ERROR":
            return f"### Jupyter Notebook (.ipynb)\n\n⚠️ Ошибка: {result['message']}\n"
        
        md = f"""### Jupyter Notebook (.ipynb)

**Файлов:** {result['files_count']}  
**Оценка nbqa+pylint:** {result['score']}/10  
**Всего проблем:** {result['total_issues']}

"""
        return md

    def _format_sql_result(self, result: dict) -> str:
        """Форматировать результаты SQL в Markdown"""
        if result["status"] == "NO_FILES":
            return "### SQL (.sql)\n\n❌ SQL файлы не найдены\n"
        
        status_emoji = "✅" if result["status"] == "PASS" else "❌"
        
        md = f"""### SQL (.sql)

**Статус:** {status_emoji} {result['status']}  
**Файлов:** {result['files_count']}  
**Всего ошибок:** {result['total_errors']}

#### Результаты по файлам:
| Файл | Диалект | Статус | Ошибок |
|------|---------|--------|--------|
"""
        for r in result.get("results", [])[:5]:
            status = "✅" if r.get("status") == "PASS" else "❌"
            errors = r.get("errors_count", r.get("message", "-"))
            md += f"| {r['file']} | {r['dialect']} | {status} | {errors} |\n"
        
        return md

    def run_tool(self, text_only: bool = False) -> dict:
        """Главная функция оценки качества кода"""
        if not self.repo:
            return {"status": 400, "answer": "Не указан репозиторий"}
        
        # Клонируем репозиторий
        clone_result = self.git_clone(self.repo, self.branch)
        if clone_result["status"] != 200:
            return clone_result
        
        local_path = clone_result["path"]
        
        # Оценка Python
        py_result = main_awerage_py(local_path, self.pylint_py)
        
        # Оценка Jupyter
        ipynb_result = main_awerage_ipynb(local_path, self.pylint_ipynb)
        
        # Оценка SQL
        sql_result = main_awerage_sql(local_path, self.pylint_sql)
        
        # Форматируем результаты
        md_report = f"""# 🔬 Оценка качества кода: {self.repo}

{self._format_py_result(py_result)}

---

{self._format_ipynb_result(ipynb_result)}

---

{self._format_sql_result(sql_result)}

---

## 📊 Сводка

| Тип файлов | Количество | Оценка |
|------------|------------|--------|
| Python | {py_result.get('files_count', 0)} | {py_result.get('score', '-')}/10 |
| Jupyter | {ipynb_result.get('files_count', 0)} | {ipynb_result.get('score', '-')}/10 |
| SQL | {sql_result.get('files_count', 0)} | {sql_result.get('status', '-')} |

"""
        
        # Сохраняем отчёт
        report_path = self.write_file_md("code_quality", self.repo, md_report)
        
        return {
            "status": 200,
            "answer": md_report,
            "report_path": report_path,
            "python": py_result,
            "jupyter": ipynb_result,
            "sql": sql_result
        }
