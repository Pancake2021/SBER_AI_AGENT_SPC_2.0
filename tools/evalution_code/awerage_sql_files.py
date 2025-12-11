"""Оценка SQL файлов с помощью sqlfluff"""
from pathlib import Path
import subprocess
import re
import chardet


def awerage_sql(repo_path: str) -> list:
    """Найти все .sql файлы в репозитории"""
    repo = Path(repo_path)
    sql_files = []
    
    for file_path in repo.rglob("*.sql"):
        if ".git" not in str(file_path):
            sql_files.append(str(file_path))
    
    return sql_files


def get_dialect(file_path: str) -> str:
    """Определить диалект SQL по содержимому файла"""
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
            encoding = chardet.detect(raw)["encoding"] or "utf-8"
        
        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            content = f.read().lower()
        
        # Эвристики для определения диалекта
        if "hive" in content or "lateral view" in content:
            return "hive"
        elif "spark" in content or "pyspark" in content:
            return "sparksql"
        elif "teradata" in content:
            return "teradata"
        elif "oracle" in content or "nvl(" in content:
            return "oracle"
        elif "postgres" in content or "serial " in content:
            return "postgres"
        else:
            return "hive"  # По умолчанию
    except Exception:
        return "hive"


def run_sqlfluff(sql_file: str, dialect: str, tox_path: str = None) -> str:
    """Запустить sqlfluff на SQL файле"""
    try:
        cmd = ["sqlfluff", "lint", f"--dialect={dialect}", sql_file]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except FileNotFoundError:
        return "ERROR: sqlfluff not installed"
    except Exception as e:
        return f"ERROR: {str(e)}"


def parse_sqlfluff_output(output: str) -> dict:
    """Парсить результаты sqlfluff"""
    errors = []
    
    lines = output.split("\n")
    for line in lines:
        # Формат: L:  1 | P:  1 | LT01 | Message
        match = re.match(r"L:\s*(\d+) \| P:\s*(\d+) \| (\w+) \| (.+)", line)
        if match:
            errors.append({
                "line": int(match.group(1)),
                "position": int(match.group(2)),
                "code": match.group(3),
                "message": match.group(4).strip()
            })
    
    # Проверяем статус
    if "PASS" in output.upper():
        status = "PASS"
    elif errors or "FAIL" in output.upper():
        status = "FAIL"
    else:
        status = "UNKNOWN"
    
    return {
        "status": status,
        "errors": errors,
        "total_issues": len(errors)
    }


def main_awerage_sql(repo_path: str, tox_path: str = None) -> dict:
    """Главная функция оценки SQL файлов"""
    sql_files = awerage_sql(repo_path)
    
    if not sql_files:
        return {
            "status": "NO_FILES",
            "message": "SQL файлы не найдены",
            "files_count": 0,
            "results": []
        }
    
    results = []
    total_errors = 0
    
    for sql_file in sql_files:
        dialect = get_dialect(sql_file)
        output = run_sqlfluff(sql_file, dialect, tox_path)
        
        if output.startswith("ERROR") or output.startswith("TIMEOUT"):
            results.append({
                "file": Path(sql_file).name,
                "dialect": dialect,
                "status": "ERROR",
                "message": output
            })
            continue
        
        parsed = parse_sqlfluff_output(output)
        total_errors += parsed["total_issues"]
        
        results.append({
            "file": Path(sql_file).name,
            "dialect": dialect,
            "status": parsed["status"],
            "errors_count": parsed["total_issues"],
            "top_errors": parsed["errors"][:5]
        })
    
    overall_status = "PASS" if total_errors == 0 else "ERRORS"
    
    return {
        "status": overall_status,
        "files_count": len(sql_files),
        "total_errors": total_errors,
        "results": results[:10]
    }
