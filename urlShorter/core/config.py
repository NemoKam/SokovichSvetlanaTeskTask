"""Модуль конфигурации приложения."""
import os

# BASE URL BLOCK
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/")


# DATABASE BLOCK
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgresql")
TEST_DATABASE_NAME = os.getenv("TEST_DATABASE_NAME", "")
DATABASE_URL_SUFFIX = (f'://{os.getenv("POSTGRES_USER")}'
                       f':{os.getenv("POSTGRES_PASSWORD")}'
                       f'@{os.getenv("POSTGRES_HOST")}'
                       f':{os.getenv("POSTGRES_PORT")}'
                       '/{}')
DATABASE_ASYNC_URL = "postgresql+asyncpg" + DATABASE_URL_SUFFIX.format(
    os.getenv("DATABASE_NAME")
)
DATABASE_SYNC_URL = "postgresql" + DATABASE_URL_SUFFIX.format(
    os.getenv("DATABASE_NAME")
)


# URLS SERVICE BLOCK
MAX_PER_PAGE_URLS_COUNT = int(os.getenv("MAX_PER_PAGE_URLS_COUNT", "50"))
MAX_GET_RANDOM_ALIAS_ATTEMPT_COUNT = int(os.getenv(
    "MAX_GET_RANDOM_ALIAS_ATTEMPT_COUNT", "5"
))

# LIMITS BLOCK
USER_CREATE_URL_IN_MINUTE_LIMIT = int(os.getenv("USER_CREATE_URL_IN_MINUTE_LIMIT", "5"))
