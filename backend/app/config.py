from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str = "mongodb://jobhunter:jobhunter@localhost:27017"
    mongo_db: str = "jobhunter"
    fetch_limit: int = 100
    telegram_token: str = ""
    telegram_chat_id: str = ""
    match_score_threshold: int = 5
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    torre_api_key: str = ""


settings = Settings()
