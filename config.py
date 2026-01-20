import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI API 配置 (用于 DeepSeek)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")

    # 应用配置
    APP_NAME: str = "DeepSeek Chat"
    APP_VERSION: str = "1.0.0"

    # 聊天配置
    DEFAULT_MODEL: str = "deepseek-chat"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
