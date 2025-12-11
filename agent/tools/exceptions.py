"""Обработчик ошибок"""


class GigaChatException(Exception):
    """Базовое исключение GigaChat"""
    pass


class BlackList(GigaChatException):
    """Исключение для чёрного списка запросов"""
    pass


class CustomError(Exception):
    """Общее пользовательское исключение"""
    pass
