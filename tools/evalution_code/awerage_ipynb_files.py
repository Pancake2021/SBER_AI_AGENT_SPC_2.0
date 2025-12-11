"""Оценка Jupyter Notebook файлов с помощью nbqa + pylint"""
from pathlib import Path
import subprocess
import re


def awerage_ipynb(repo_path: str) -> list:
    """Найти все .ipynb файлы в репозитории"""
    repo = Path(repo_path)
    ipynb_files = []
    
    for file_path in repo.rglob("*.ipynb"):
        if ".git" not in str(file_path) and ".ipynb_checkpoints" not in str(file_path):
            ipynb_files.append(str(file_path))
    
    return ipynb_files


def run_nbqa(ipynb_files: list, pylintrc: str) -> str:
    """Запустить nbqa + pylint на Jupyter файлах"""
    if not ipynb_files:
        return ""
    
    try:
        result = subprocess.run(
            ["nbqa", "pylint", f"--rcfile={pylintrc}"] + ipynb_files,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT: nbqa execution exceeded 5 minutes"
    except FileNotFoundError:
        return "ERROR: nbqa or pylint not installed"
    except Exception as e:
        return f"ERROR: {str(e)}"


def parse_file_nbqa(output: str) -> dict:
    """Парсить результаты nbqa"""
    errors = {
        "convention": 0,
        "warning": 0,
        "error": 0,
        "fatal": 0,
        "refactor": 0,
        "info": 0
    }
    
    messages = []
    
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
        match = re.match(r".+:\d+:\d+: ([CWEFRIV])(\d+): (.+)", line)
        if match:
            msg_type = patterns.get(match.group(1), "info")
            errors[msg_type] += 1
            messages.append({
                "type": msg_type,
                "code": f"{match.group(1)}{match.group(2)}",
                "message": match.group(3)
            })
    
    score_match = re.search(r"Your code has been rated at ([\d.]+)/10", output)
    score = float(score_match.group(1)) if score_match else 0.0
    
    return {
        "errors": errors,
        "messages": messages[:20],
        "score": score,
        "total_issues": sum(errors.values())
    }


def main_awerage_ipynb(repo_path: str, pylintrc: str) -> dict:
    """Главная функция оценки Jupyter файлов"""
    ipynb_files = awerage_ipynb(repo_path)
    
    if not ipynb_files:
        return {
            "status": "NO_FILES",
            "message": "Jupyter Notebook файлы не найдены",
            "files_count": 0,
            "score": None
        }
    
    output = run_nbqa(ipynb_files, pylintrc)
    
    if output.startswith("ERROR") or output.startswith("TIMEOUT"):
        return {
            "status": "ERROR",
            "message": output,
            "files_count": len(ipynb_files),
            "score": None
        }
    
    parsed = parse_file_nbqa(output)
    
    return {
        "status": "OK",
        "files_count": len(ipynb_files),
        "files": [Path(f).name for f in ipynb_files[:10]],
        "score": parsed["score"],
        "total_issues": parsed["total_issues"],
        "errors": parsed["errors"],
        "top_messages": parsed["messages"][:10]
    }
