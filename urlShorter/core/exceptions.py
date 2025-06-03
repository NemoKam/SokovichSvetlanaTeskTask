"""Модуль кастомных ошибок."""
from fastapi import HTTPException


class AliasNotFoundException(HTTPException):
    """Alias not found exception."""

    def __init__(self) -> None:
        """Функция __init__ для кастомной ошибки."""
        self.status_code=404
        self.detail="Alias not found"

class ShortUrlCreatingException(HTTPException):
    """Short Url creating exception."""

    def __init__(self, detail: str) -> None:
        """Функция __init__ для кастомной ошибки."""
        self.status_code=400
        self.detail=detail

class UnexpectedException(HTTPException):
    """Unexcpected exception."""

    def __init__(self, detail: str) -> None:
        """Функция __init__ для кастомной ошибки."""
        self.status_code=500
        self.detail=detail

class InvalidConnectingClientException(HTTPException):
    """Invalid client connecting exception."""

    def __init__(self) -> None:
        """Функция __init__ для кастомной ошибки."""
        self.status_code = 500
        self.detail="Invalid connection"

class UserCreateUrlLimitExceedException(HTTPException):
    """User exceeded limits for url creation exception."""

    def __init__(self) -> None:
        """Функция __init__ для кастомной ошибки."""
        self.status_code = 429
        self.detail="Too many requests."
