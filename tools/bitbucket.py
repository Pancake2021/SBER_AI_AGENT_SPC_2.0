"""Модуль для работы с BitBucket и GitHub API"""
import requests
from tools.settings import Configure
from tools.github_client import GitHubAPI
from loguru import logger


class ConnectionAPI(Configure):
    """
    Класс для подключения к VCS (BitBucket или GitHub).
    Автоматически выбирает провайдера на основе конфигурации.
    """

    def __init__(self):
        super().__init__()
        # Инициализируем GitHub клиент, если выбран этот провайдер
        self.github_client = GitHubAPI() if self.provider == "github" else None

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

    def read_file_bb(self, data):
        """Чтение файла"""
        if self.provider == "github":
            return self.github_client.read_file_bb(data)

        # BitBucket Logic
        repository = data["repository"]
        file_path = data["file_path"]
        
        if not self.token_bb:
             return {"status": 400, "answer": "Нет токена BitBucket и GitHub. Проверьте .env"}

        headers = {"Authorization": f"Bearer {self.token_bb}"}
        url = f"{self.main_url}/{self.project_bb}/repos/{repository}/raw/{file_path}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return {"status": 200, "answer": response.text}
            else:
                return {"status": response.status_code, "answer": response.text}
        except Exception as e:
            logger.error(f"Error BitBucket: {e}")
            return {"status": 500, "answer": str(e)}

    def get_files(self, name_repository):
        """Получение списка файлов"""
        if self.provider == "github":
            return self.github_client.get_files(name_repository)
            
        # BitBucket Logic
        if not self.token_bb:
             return {"status": 400, "answer": "Нет токена BitBucket и GitHub. Проверьте .env"}

        headers = {"Authorization": f"Bearer {self.token_bb}"}
        url = f"{self.main_url}/{self.project_bb}/repos/{name_repository}/files?limit=100000"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {"status": 200, "answer": data["values"]}
            else:
                return {"status": response.status_code, "answer": response.text}
        except Exception as e:
            logger.error(f"Error BitBucket: {e}")
            return {"status": 500, "answer": str(e)}

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

    def create_pull_request(self, repository, title, description, source_branch, destination_branch="master"):
        if self.provider == "github":
            return {"status": 501, "answer": "Create PR not implemented for GitHub yet"}
        
        # ... (старый код BitBucket) ...
        headers = {"Authorization": f"Bearer {self.token_bb}"}
        url = f"{self.main_url}/{self.project_bb}/repos/{repository}/pull-requests"
        data = {
            "title": title,
            "description": description,
            "state": "OPEN",
            "open": True,
            "closed": False,
            "fromRef": {
                "id": f"refs/heads/{source_branch}",
                "repository": {
                    "slug": repository,
                    "name": None,
                    "project": {
                        "key": self.project_bb
                    }
                }
            },
            "toRef": {
                "id": f"refs/heads/{destination_branch}",
                "repository": {
                    "slug": repository,
                    "name": None,
                    "project": {
                        "key": self.project_bb
                    }
                }
            },
            "locked": False,
            "reviewers": [
                {
                    "user": {
                        "name": self.user_bb
                    }
                }
            ]
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                return {"status": 201, "answer": "Pull request created"}
            else:
                return {"status": response.status_code, "answer": response.text}
        except Exception as e:
            logger.error(f"Error BitBucket: {e}")
            return {"status": 500, "answer": str(e)}

    def get_pull_request(self, repository, pull_request_id):
        if self.provider == "github":
             return {"status": 501, "answer": "Get PR not implemented for GitHub yet"}

        headers = {"Authorization": f"Bearer {self.token_bb}"}
        url = f"{self.main_url}/{self.project_bb}/repos/{repository}/pull-requests/{pull_request_id}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return {"status": 200, "answer": response.json()}
            else:
                return {"status": response.status_code, "answer": response.text}
        except Exception as e:
            logger.error(f"Error BitBucket: {e}")
            return {"status": 500, "answer": str(e)}

    def comment_pull_request(self, repository, pull_request_id, text):
        if self.provider == "github":
             return {"status": 501, "answer": "Comment PR not implemented for GitHub yet"}

        headers = {"Authorization": f"Bearer {self.token_bb}"}
        url = f"{self.main_url}/{self.project_bb}/repos/{repository}/pull-requests/{pull_request_id}/comments"
        data = {"text": text}
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                return {"status": 201, "answer": "Comment created"}
            else:
                return {"status": response.status_code, "answer": response.text}
        except Exception as e:
            logger.error(f"Error BitBucket: {e}")
            return {"status": 500, "answer": str(e)}
            
    def comment_line_code(self, repository, pull_request_id, text, path, line):
        if self.provider == "github":
             return {"status": 501, "answer": "Comment Line not implemented for GitHub yet"}

        headers = {"Authorization": f"Bearer {self.token_bb}"}
        url = f"{self.main_url}/{self.project_bb}/repos/{repository}/pull-requests/{pull_request_id}/comments"
        data = {
            "text": text,
            "anchor": {
                "line": line,
                "lineType": "ADDED",
                "fileType": "TO",
                "path": path,
                "srcPath": path
            }
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                return {"status": 201, "answer": "Comment created"}
            else:
                return {"status": response.status_code, "answer": response.text}
        except Exception as e:
            logger.error(f"Error BitBucket: {e}")
            return {"status": 500, "answer": str(e)}

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
