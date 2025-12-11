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
        self.token_bb = os.getenv('TOKEN_BITBUCKET')
        self.login = os.getenv('LOGIN')
        self.psw = os.getenv('PSW')
        
        # Пути к файлам и моделям
        self.gen_readme_path = os.getenv('PATH_FILE', 'output/readme_test/')
        self.clone_repo_path = os.getenv('PATH_CLONE', 'output/clone_repo/')
        self.path_pickle = os.getenv('PATH_PICKLE_FILE', '/home/datalab/vect_bge.pkl')
        self.path_card = os.getenv('PATH_BASE_CARD', '/home/datalab/')
        self.path_lint = os.getenv('PATH_ERRORS_FILE', 'tools/evalution_code/errors/')
        self.path_model = os.getenv('PATH_MODEL_M3')
        
        # Пути к конфигам для linters
        self.pylint_py = os.getenv('PYLINTRC', 'tools/evalution_code/config/pylintrc')
        self.pylint_ipynb = os.getenv('PYLINTRC_IPYNB', 'tools/evalution_code/config/pylintrc_ipynb')
        self.pylint_sql = os.getenv('TOX', 'tools/evalution_code/config/tox.ini')
        
        # BitBucket project
        self.bb_project = os.getenv('GIT_NAME_PROJECT_BB')
        self.bb_user = f"~{os.getenv('GIT_NAME_USER_BB')}"
        self.proj = self.bb_project if self.bb_project else self.bb_user
        
        # API URLs и параметры
        self.main_url = 'https://df-bitbucket.ca.sbrf.ru'
        self.auth = (self.login, self.psw)
        self.params = {'limit': 9999}
        self.headers = {
            'Content-Type': 'application/json',
        }
        
        # Проверка конфигурации
        _ = True if (
            self.bb_project or os.getenv('GIT_NAME_USER_BB')
        ) else self._error_project_url()
        
        _ = True if self._check_auth() else self._error_connection()

    def _check_admin_token(self, repo: str) -> bool:
        """Проверка что токен BB является с правами ADMIN"""
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
