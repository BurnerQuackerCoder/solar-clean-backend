import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Solar Dispatch System"

    TELEGRAM_BOT_TOKEN: str = str(os.getenv("TELEGRAM_BOT_TOKEN"))

    SUPABASE_URL: str = str(os.getenv("SUPABASE_URL"))
    SUPABASE_KEY: str = str(os.getenv("SUPABASE_KEY"))

    class Config:
        case_sensitive = True

settings = Settings()