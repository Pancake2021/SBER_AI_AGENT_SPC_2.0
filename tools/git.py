"""Git операции для работы с репозиториями"""
from tools.bitbucket import ConnectionAPI
from git import Repo
from pathlib import Path
import shutil
import os


class Git(ConnectionAPI):
    """Класс для Git операций"""

    def __init__(self):
        super().__init__()

    def git_clone(self, repo: str, branch: str = '') -> dict:
        """Клонирование репозитория из BitBucket"""
        clone_path = Path(self.clone_repo_path) / repo
        
        # Удалить если существует
        if clone_path.exists():
            self._dell_repo(repo)
        
        # Формируем URL
        clone_url = f'{self.main_url}/scm/{self.proj}/{repo}.git'
        
        try:
            if branch:
                Repo.clone_from(
                    clone_url,
                    clone_path,
                    branch=branch,
                    env={
                        'GIT_ASKPASS': 'echo',
                        'GIT_USERNAME': self.login,
                        'GIT_PASSWORD': self.psw
                    }
                )
            else:
                Repo.clone_from(
                    clone_url,
                    clone_path,
                    env={
                        'GIT_ASKPASS': 'echo',
                        'GIT_USERNAME': self.login,
                        'GIT_PASSWORD': self.psw
                    }
                )
            return {"status": 200, "answer": f"Репозиторий {repo} успешно склонирован", "path": str(clone_path)}
        except Exception as e:
            return {"status": 500, "answer": f"Ошибка клонирования: {str(e)}"}

    def ensure_branch_and_update(self, repo: str, branch: str) -> dict:
        """Переключение на ветку и обновление"""
        clone_path = Path(self.clone_repo_path) / repo
        
        if not clone_path.exists():
            return {"status": 404, "answer": "Репозиторий не найден локально"}
        
        try:
            git_repo = Repo(clone_path)
            
            # Получаем все ветки
            git_repo.remotes.origin.fetch()
            
            # Переключаемся на ветку
            if branch in [ref.name.split('/')[-1] for ref in git_repo.remotes.origin.refs]:
                git_repo.git.checkout(branch)
                git_repo.remotes.origin.pull()
                return {"status": 200, "answer": f"Переключено на ветку {branch}"}
            else:
                return {"status": 404, "answer": f"Ветка {branch} не найдена"}
        except Exception as e:
            return {"status": 500, "answer": f"Ошибка: {str(e)}"}

    def _dell_repo(self, repo: str) -> dict:
        """Удаление локального репозитория"""
        clone_path = Path(self.clone_repo_path) / repo
        
        if clone_path.exists():
            try:
                shutil.rmtree(clone_path)
                return {"status": 200, "answer": f"Репозиторий {repo} удалён"}
            except Exception as e:
                return {"status": 500, "answer": f"Ошибка удаления: {str(e)}"}
        return {"status": 404, "answer": "Репозиторий не найден"}

    def get_local_files(self, repo: str) -> list:
        """Получить список файлов локального репозитория"""
        clone_path = Path(self.clone_repo_path) / repo
        
        if not clone_path.exists():
            return []
        
        files = []
        for root, dirs, filenames in os.walk(clone_path):
            # Исключаем .git
            dirs[:] = [d for d in dirs if d != '.git']
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), clone_path)
                files.append(rel_path)
        return files
