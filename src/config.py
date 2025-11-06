from pydantic_settings import BaseSettings
from pathlib import Path



## AWS RDS Postgres Configuration ######
# class Settings(BaseSettings):
#     POSTGRES_USER: str
#     POSTGRES_PASSWORD: str
#     POSTGRES_DB: str
#     POSTGRES_HOST: str
#     DATABASE_PORT: int

#     model_config = {
#         "env_file": str(Path(__file__).parent / ".env"),
#         "env_file_encoding": "utf-8", ## avoid issues with special characters in passwords
#         "extra": "ignore"
#     }



#     @property
#     def DATABASE_URL(self) -> str:
#         # The @property decorator in Python turns a method into a read-only attribute.
#         # That means:
#         # - You define it like a function, but
#         # - You access it like a variable.
#         return (
#             f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
#             f"@{self.POSTGRES_HOST}:{self.DATABASE_PORT}/{self.POSTGRES_DB}"
#         )



# Config = Settings()




#### Neon Postgres Configuration ######
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """
    App config for Neon.
    DATABASE_URL is required and loaded from .env
    """
    DATABASE_URL: str
    JWT_SECRET : str
    JWT_ALGORITHM : str    

    AWS_S3_BUCKET_NAME: str
    AWS_S3_REGION: str = "ap-southeast-1"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    model_config = {
        # .env is in the same folder as config.py
        "env_file": str(Path(__file__).parent / ".env"),
        "env_file_encoding": "utf-8", ## avoid issues with special characters in passwords.
        "extra": "ignore"
    }

Config = Settings()


