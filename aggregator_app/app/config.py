"""Конфигурация приложения."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL


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
        url = URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_username.get_secret_value(),
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_database_name,
        )
        return str(url)


settings = Settings()
