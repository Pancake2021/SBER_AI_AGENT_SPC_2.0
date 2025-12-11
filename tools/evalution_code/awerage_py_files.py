"""Оценка Python файлов с помощью pylint"""
from pathlib import Path
import subprocess
import re


def awerage_py(repo_path: str) -> list:
    """Найти все .py файлы в репозитории"""
    repo = Path(repo_path)
    py_files = []
    
    for file_path in repo.rglob("*.py"):
        if ".git" not in str(file_path):
            py_files.append(str(file_path))
    
    return py_files


def run_pylint(py_files: list, pylintrc: str) -> str:
    """Запустить pylint на Python файлах"""
    if not py_files:
        return ""
    
    try:
        result = subprocess.run(
            ["pylint", f"--rcfile={pylintrc}"] + py_files,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT: pylint execution exceeded 5 minutes"
    except FileNotFoundError:
        return "ERROR: pylint not installed"
    except Exception as e:
        return f"ERROR: {str(e)}"


def parse_file_pylint(output: str) -> dict:
    """Парсить результаты pylint"""
    errors = {
        "convention": 0,
        "warning": 0,
        "error": 0,
        "fatal": 0,
        "refactor": 0,
        "info": 0
    }
    
    messages = []
    
    # Паттерны для разных типов сообщений
    patterns = {
        "C": "convention",
        "W": "warning",
        "E": "error",
        "F": "fatal",
        "R": "refactor",
        "I": "info"
    }
    
    lines = output.split("\n")
    for line in lines:
        # Формат: file.py:line:col: CXXXX: message (category)
        match = re.match(r".+:\d+:\d+: ([CWEFRIV])(\d+): (.+)", line)
        if match:
            msg_type = patterns.get(match.group(1), "info")
            errors[msg_type] += 1
            messages.append({
                "type": msg_type,
                "code": f"{match.group(1)}{match.group(2)}",
                "message": match.group(3)
            })
    
    # Парсим финальную оценку
    score_match = re.search(r"Your code has been rated at ([\d.]+)/10", output)
    score = float(score_match.group(1)) if score_match else 0.0
    
    return {
        "errors": errors,
        "messages": messages[:20],  # Ограничение
        "score": score,
        "total_issues": sum(errors.values())
    }


def main_awerage_py(repo_path: str, pylintrc: str) -> dict:
    """Главная функция оценки Python файлов"""
    py_files = awerage_py(repo_path)
    
    if not py_files:
        return {
            "status": "NO_FILES",
            "message": "Python файлы не найдены",
            "files_count": 0,
            "score": None
        }
    
    output = run_pylint(py_files, pylintrc)
    
    if output.startswith("ERROR") or output.startswith("TIMEOUT"):
        return {
            "status": "ERROR",
            "message": output,
            "files_count": len(py_files),
            "score": None
        }
    
    parsed = parse_file_pylint(output)
    
    return {
        "status": "OK",
        "files_count": len(py_files),
        "files": [Path(f).name for f in py_files[:10]],
        "score": parsed["score"],
        "total_issues": parsed["total_issues"],
        "errors": parsed["errors"],
        "top_messages": parsed["messages"][:10]
    }
