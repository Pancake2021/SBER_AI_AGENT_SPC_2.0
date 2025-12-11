"""Клиент для работы с GitHub API"""
import requests
import base64
from tools.settings import Configure
from loguru import logger


class GitHubAPI(Configure):
    """Класс для взаимодействия с GitHub API"""

    def __init__(self):
        super().__init__()
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_files(self, repo_name: str) -> dict:
        """
        Получение списка файлов репозитория (рекурсивно)
        
        Args:
            repo_name: Имя репозитория
            
        Returns:
            dict: Список файлов или ошибка
        """
        if not self.github_token:
            return {"status": 400, "answer": "GITHUB_TOKEN не найден"}

        # Используем Git Trees API для рекурсивного получения всех файлов
        # Сначала получаем default branch
        repo_url = f"{self.main_url}/repos/{self.github_owner}/{repo_name}"
        
        try:
            # 1. Получаем инфо о репозитории (чтобы узнать default branch)
            resp = requests.get(repo_url, headers=self.headers)
            if resp.status_code != 200:
                return {"status": resp.status_code, "answer": f"Ошибка доступа к репозиторию: {resp.text}"}
            
            repo_info = resp.json()
            default_branch = repo_info.get("default_branch", "main")
            
            # 2. Получаем дерево файлов
            tree_url = f"{repo_url}/git/trees/{default_branch}?recursive=1"
            resp = requests.get(tree_url, headers=self.headers)
            
            if resp.status_code != 200:
                return {"status": resp.status_code, "answer": f"Ошибка получения списка файлов: {resp.text}"}
            
            tree_data = resp.json()
            
            files = []
            for item in tree_data.get("tree", []):
                if item["type"] == "blob":  # Только файлы
                    files.append(item["path"])
            
            return {
                "status": 200,
                "answer": files[:1000]  # Ограничиваем кол-во файлов
            }
            
        except Exception as e:
            logger.error(f"GitHub API Error: {e}")
            return {"status": 500, "answer": f"Ошибка GitHub API: {str(e)}"}

    def read_file_bb(self, data: dict) -> dict:
        """
        Чтение файла из GitHub
        (Название метода сохранено для совместимости с ConnectionAPI)
        
        Args:
            data: {"repository": str, "file_path": str}
        """
        repo_name = data.get("repository")
        file_path = data.get("file_path")
        
        if not repo_name or not file_path:
            return {"status": 400, "answer": "Не указан repository или file_path"}
            
        url = f"{self.main_url}/repos/{self.github_owner}/{repo_name}/contents/{file_path}"
        
        try:
            resp = requests.get(url, headers=self.headers)
            
            if resp.status_code != 200:
                return {"status": resp.status_code, "answer": f"Ошибка чтения файла: {resp.text}"}
            
            content_data = resp.json()
            
            # GitHub возвращает контент в base64
            if "content" in content_data and content_data["encoding"] == "base64":
                file_content = base64.b64decode(content_data["content"]).decode("utf-8", errors="ignore")
                return {
                    "status": 200,
                    "answer": file_content
                }
            else:
                return {"status": 400, "answer": "Не удалось декодировать файл (возможно он пустой или не base64)"}
                
        except Exception as e:
            logger.error(f"GitHub API Error: {e}")
            return {"status": 500, "answer": f"Ошибка GitHub API: {str(e)}"}
