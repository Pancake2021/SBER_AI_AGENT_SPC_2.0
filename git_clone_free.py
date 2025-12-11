"""Автоаутентификация Git для BitBucket"""
from pathlib import Path
import os
import subprocess


class RunningTheScript:
    """Класс для настройки Git аутентификации"""

    def __init__(self, login: str = None, password: str = None):
        self.login = login or os.getenv("LOGIN")
        self.password = password or os.getenv("PSW")
        self.home = Path.home()

    def create_git_files(self) -> dict:
        """Создание .gitconfig и .git-credentials файлов"""
        if not self.login or not self.password:
            return {"status": 400, "answer": "Не указаны логин или пароль"}
        
        try:
            # Создание .gitconfig
            gitconfig_path = self.home / ".gitconfig"
            gitconfig_content = f"""[user]
    name = {self.login}
    email = {self.login}@sberbank.ru
[credential]
    helper = store
[http]
    sslVerify = false
"""
            with open(gitconfig_path, "w", encoding="utf-8") as f:
                f.write(gitconfig_content)
            
            # Создание .git-credentials
            credentials_path = self.home / ".git-credentials"
            credentials_content = f"https://{self.login}:{self.password}@df-bitbucket.ca.sbrf.ru\n"
            
            with open(credentials_path, "w", encoding="utf-8") as f:
                f.write(credentials_content)
            
            # Установка прав доступа
            os.chmod(credentials_path, 0o600)
            
            return {
                "status": 200,
                "answer": "Git файлы успешно созданы",
                "files": [str(gitconfig_path), str(credentials_path)]
            }
        
        except Exception as e:
            return {"status": 500, "answer": f"Ошибка: {str(e)}"}

    def _check_password(self) -> bool:
        """Проверка корректности пароля через тестовый запрос"""
        try:
            result = subprocess.run(
                ["git", "ls-remote", "https://df-bitbucket.ca.sbrf.ru/scm/sva_code/test.git"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0 or "Authentication" not in result.stderr
        except Exception:
            return False

    def git(self) -> dict:
        """Главная функция настройки Git"""
        # Проверка наличия логина и пароля
        if not self.login or not self.password:
            return {"status": 400, "answer": "Логин или пароль не указаны"}
        
        # Создание файлов
        result = self.create_git_files()
        if result["status"] != 200:
            return result
        
        # Настройка Git глобально
        try:
            subprocess.run(
                ["git", "config", "--global", "credential.helper", "store"],
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                ["git", "config", "--global", "http.sslVerify", "false"],
                capture_output=True,
                timeout=10
            )
        except Exception:
            pass
        
        return {
            "status": 200,
            "answer": "Git аутентификация настроена успешно"
        }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    script = RunningTheScript()
    result = script.git()
    print(result)
