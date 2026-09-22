"""The only place that talks to Azure OpenAI.

Keeping this in one small module makes it easy to swap the model, add
caching, or mock it in tests.
"""
import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AzureOpenAI,
    RateLimitError,
)

from config import Settings

log = logging.getLogger(__name__) #lets this file write to the logs

#Create our own error type:LLMError
class LLMError(Exception):
    """Raised with a safe, user-facing message. Details go to the logs only."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code

#create the connection to Azure, using the settings from .env :
class LLMClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            timeout=settings.llm_timeout_seconds, #if Azure doesn't answer in 30 seconds, stop waiting.
            max_retries=2,#if Azure fails for a moment, try again up to 2 times automatically.
        )

#sends the message to the model (It sends 2 messages):
    def chat(self, system_prompt: str, user_message: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._settings.azure_openai_deployment, #The deployment name (not the model name)
                messages=[
                    {"role": "system", "content": system_prompt}, #The system message is the instructions
                    {"role": "user", "content": user_message},#The user message is what the person typed.
                ]
            )
        #If Azure fails, we catch the error and raise our own LLMError with a safe message.
        except RateLimitError as exc:
            log.warning("LLM rate limited: %s", exc)
            raise LLMError("The AI service is busy. Try again in a moment.", 503) from exc
        except APITimeoutError as exc:
            log.warning("LLM timeout: %s", exc)
            raise LLMError("The AI service took too long to answer.", 504) from exc
        except APIConnectionError as exc:
            log.error("LLM connection error: %s", exc)
            raise LLMError("Could not reach the AI service.", 502) from exc
        except APIStatusError as exc:
            # 401 = bad key, 404 = wrong deployment name, 410 = retired model.
            log.error("LLM returned %s: %s", exc.status_code, exc)
            raise LLMError("The AI service returned an error.", 502) from exc
        #takes the answer text out of Azure's response.
        return response.choices[0].message.content or "" #or "" makes sure we return empty text instead of crashing if the answer is empty.
