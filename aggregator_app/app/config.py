"""Конфигурация приложения."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения.

    Атрибуты:
    - `postgres_username` - Имя пользователя для подключения к базе данных.
    - `postgres_password` - Пароль для подключения к базе данных.
    - `postgres_database_name` - Имя базы данных.
    - `postgres_host` - Хост для подключения к базе данных.
    - `postgres_port` - Порт для подключения к базе данных.
    - `lms_api_key` - API ключ для доступа к LMS.

    Свойства:
    - `database_url` - URL для подключения к базе данных.

    """

    postgres_username: SecretStr
    postgres_password: SecretStr
    postgres_database_name: str
    postgres_host: str
    postgres_port: int
    lms_api_key: SecretStr

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_username.get_secret_value()}",
            f":{self.postgres_password.get_secret_value()}",
            f"@{self.postgres_host}",
            f":{self.postgres_port}",
            f"/{self.postgres_database_name}",
        )


settings = Settings()
