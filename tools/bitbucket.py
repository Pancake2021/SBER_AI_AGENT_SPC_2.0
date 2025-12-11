"""BitBucket API Integration"""
from tools.settings import Configure
import requests


class ConnectionAPI(Configure):
    """Класс для работы с BitBucket API"""

    def __init__(self):
        super().__init__()

    def get_requests(self, url: str) -> dict:
        """GET запрос к BitBucket API"""
        response = requests.get(
            self.main_url + url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            params=self.params,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return {"error": f"Status code: {response.status_code}"}

    def read_file_bb(self, data: dict) -> dict:
        """Чтение файла из репозитория BitBucket"""
        repo = data.get("repository")
        file_path = data.get("file_path")
        branch = data.get("branch", "master")
        
        url = f'/rest/api/1.0/projects/{self.proj}/repos/{repo}/browse/{file_path}'
        params = {'at': branch, 'limit': 9999}
        
        response = requests.get(
            self.main_url + url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            lines = data.get("lines", [])
            content = "\n".join([line.get("text", "") for line in lines])
            return {"status": 200, "answer": content}
        return {"status": 404, "answer": f"Файл не найден: {file_path}"}

    def get_files(self, repo: str, path: str = "", branch: str = "master") -> dict:
        """Получить список файлов репозитория"""
        url = f'/rest/api/1.0/projects/{self.proj}/repos/{repo}/files/{path}'
        params = {'at': branch, 'limit': 9999}
        
        response = requests.get(
            self.main_url + url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            files = data.get("values", [])
            return {"status": 200, "answer": files}
        return {"status": 404, "answer": f"Репозиторий не найден: {repo}"}

    def get_files_repo_awerage(self, repo: str) -> bool:
        """Проверка наличия кода в репозитории"""
        result = self.get_files(repo)
        if result["status"] == 200:
            files = result["answer"]
            code_extensions = ['.py', '.ipynb', '.sql']
            for f in files:
                if any(f.endswith(ext) for ext in code_extensions):
                    return True
        return False

    def get_description_repo(self, repo: str) -> dict:
        """Получить описание репозитория"""
        url = f'/rest/api/1.0/projects/{self.proj}/repos/{repo}'
        response = requests.get(
            self.main_url + url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": 200,
                "answer": {
                    "name": data.get("name"),
                    "description": data.get("description", ""),
                    "project": data.get("project", {}).get("key")
                }
            }
        return {"status": 404, "answer": "Репозиторий не найден"}

    def get_repos_list(self) -> dict:
        """Получить список репозиториев проекта"""
        url = f'/rest/api/1.0/projects/{self.proj}/repos'
        response = requests.get(
            self.main_url + url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            params=self.params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            repos = [r.get("slug") for r in data.get("values", [])]
            return {"status": 200, "answer": repos}
        return {"status": 404, "answer": "Проект не найден"}

    def get_commits(self, repo: str, first: bool = True) -> dict:
        """Получить коммиты репозитория"""
        url = f'/rest/api/1.0/projects/{self.proj}/repos/{repo}/commits'
        params = {'limit': 1 if first else 9999}
        
        response = requests.get(
            self.main_url + url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            commits = data.get("values", [])
            return {"status": 200, "answer": commits}
        return {"status": 404, "answer": "Коммиты не найдены"}

    def _get_main_user(self, repo: str, commits: list) -> dict:
        """Получить статистику изменений по пользователям"""
        users = {}
        for commit in commits:
            author = commit.get("author", {}).get("name", "Unknown")
            if author not in users:
                users[author] = 0
            users[author] += 1
        return users

    def get_login_user(self, name_user: str) -> dict:
        """Получить логин пользователя по ФИО"""
        url = f'/rest/api/1.0/users?filter={name_user}'
        response = requests.get(
            self.main_url + url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("values", [])
            if users:
                return {"status": 200, "answer": users[0].get("slug")}
        return {"status": 404, "answer": "Пользователь не найден"}

    def get_users_permission(self, repo: str, gen: bool = False) -> dict:
        """Получить права доступа пользователей к репозиторию"""
        url = f'/rest/api/1.0/projects/{self.proj}/repos/{repo}/permissions/users'
        response = requests.get(
            self.main_url + url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            params=self.params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("values", [])
            permissions = []
            for user in users:
                permissions.append({
                    "user": user.get("user", {}).get("slug"),
                    "permission": user.get("permission")
                })
            return {"status": 200, "answer": permissions}
        return {"status": 404, "answer": "Права не найдены"}
