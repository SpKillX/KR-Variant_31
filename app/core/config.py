from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@db:5432/restaurant_db"
    SECRET_KEY: str = "super-secret-key-for-course-project-12345"
    
    # Booking constraints (in minutes)
    MIN_BOOKING_DURATION: int = 60
    MAX_BOOKING_DURATION: int = 240

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

