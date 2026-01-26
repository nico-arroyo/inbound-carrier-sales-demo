from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_keys: str = Field(..., alias="API_KEYS")
    fmcsa_webkey: str | None = Field(default=None, alias="FMCSA_WEBKEY")
    loads_file: str = Field(default="loads.seed.json", alias="LOADS_FILE")

    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}


settings = Settings()
