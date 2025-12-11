"""Конфигурация и загрузка переменных окружения"""
from dotenv import load_dotenv
import warnings
import os
import requests


class Configure:
    """Конфигурационные опции для работы с BitBucket и инструментами"""

    def __init__(self):
        warnings.filterwarnings('ignore')
        load_dotenv('env')
        
        # BitBucket credentials
        # BitBucket
        self.token_bb = os.getenv("TOKEN_BITBUCKET")
        self.login = os.getenv("LOGIN")
        self.password = os.getenv("PSW")
        self.psw = self.password  # Alias for backward compatibility
        self.project_bb = os.getenv("GIT_NAME_PROJECT_BB")
        self.user_bb = os.getenv("GIT_NAME_USER_BB")
        
        # GitHub
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_owner = os.getenv("GITHUB_OWNER")  # Пользователь или организация
        
        # Определение провайдера
        if self.token_bb:
            self.provider = "bitbucket"
            self.main_url = "https://df-bitbucket.ca.sbrf.ru/rest/api/1.0/projects"
        elif self.github_token:
            self.provider = "github"
            self.main_url = "https://api.github.com"
        else:
            self.provider = "unknown"
            # Не кидаем ошибку сразу, возможно работаем локально
            self.main_url = ""

        # Paths
        self.path_model = os.getenv("PATH_MODEL_M3")
        self.path_pickle = os.getenv("PATH_PICKLE_FILE", '/home/datalab/vect_bge.pkl')
        self.path_card = os.getenv('PATH_BASE_CARD', '/home/datalab/')
        self.path_lint = os.getenv('PATH_ERRORS_FILE', 'tools/evalution_code/errors/')
        
        # Пути к конфигам для linters
        self.pylint_py = os.getenv('PYLINTRC', 'tools/evalution_code/config/pylintrc')
        self.pylint_ipynb = os.getenv('PYLINTRC_IPYNB', 'tools/evalution_code/config/pylintrc_ipynb')
        self.pylint_sql = os.getenv('TOX', 'tools/evalution_code/config/tox.ini')
        
        # BitBucket project (для совместимости со старым кодом)
        self.bb_project = os.getenv('GIT_NAME_PROJECT_BB')
        self.bb_user = f"~{os.getenv('GIT_NAME_USER_BB', '')}"
        self.proj = self.bb_project if self.bb_project else self.bb_user
        
        # API URLs и параметры (только для BitBucket)
        if self.provider == "bitbucket":
            self.auth = (self.login, self.psw)
            self.params = {'limit': 9999}
            self.headers = {
                'Content-Type': 'application/json',
            }
            
            # Проверка конфигурации только для BitBucket
            if not (self.bb_project or os.getenv('GIT_NAME_USER_BB')):
                self._error_project_url()
            
            # Проверка подключения к BitBucket (отключено для ускорения)
            # _ = True if self._check_auth() else self._error_connection()
        else:
            # GitHub или локальный режим - не требуем BB переменных
            self.auth = None
            self.params = {}
            self.headers = {}

    def _check_admin_token(self, repo: str) -> bool:
        """Проверка что токен BB является с правами ADMIN"""
        if self.provider != "bitbucket":
            return True  # Для GitHub пока не проверяем
        url = f'/rest/api/1.0/projects/{self.proj}/repos/{repo}/permissions/users'
        check = requests.get(
            self.main_url+url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            timeout=20
        )
        if check.status_code != 200:
            return False
        return True

    def _check_auth(self) -> bool:
        """Проверка данных BitBucket"""
        if self.provider != "bitbucket":
            return True  # Для GitHub не проверяем через этот метод
        url = f'/rest/api/1.0/projects/{self.proj}'
        check = requests.get(
            self.main_url+url,
            verify=False,
            headers=self.headers,
            auth=self.auth,
            timeout=20
        )
        if check.status_code != 200:
            self._error_connection()
        return True

    def _error_connection(self):
        raise ValueError('Данные (логин, пароль) введены неверно')

    def _error_project_url(self):
        raise ValueError('Не указан ни один параметр: GIT_NAME_PROJECT_BB или GIT_NAME_USER_BB')

    def _error_admin(self):
        raise ValueError('У токена нет прав администратора')

