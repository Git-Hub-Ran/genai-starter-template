"""App settings, read from environment variables (or a local .env file).

Secrets never live in code. Locally they come from .env; on Azure they come
from App Service settings (ideally a Key Vault reference).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

#lists every setting the app needs, like the endpoint, key, and deployment name:
class Settings(BaseSettings): 
    model_config = SettingsConfigDict(env_file=".env", extra="ignore") #if .env has a setting we don't use, ignore it instead of crashing.

    azure_openai_endpoint: str = ""  # e.g. https://<resource>.openai.azure.com
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-5.4-mini"
    azure_openai_api_version: str = "2025-04-01-preview"

    # Comma-separated list of frontend URLs allowed to call this API.
    allowed_origins: str = "http://localhost:8501"
    max_input_chars: int = 4000
    llm_timeout_seconds: float = 30.0

    @property#makes the function readable like a value.
    #origins turns the text "url1,url2" into a list.
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property#makes the function readable like a value.
    def llm_configured(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)#it is True only if both the endpoint and key are filled in.


#reads the settings once and remembers them. It doesn't read the file again on every request.
@lru_cache #makes the function remember its result.
def get_settings() -> Settings:
    return Settings()
