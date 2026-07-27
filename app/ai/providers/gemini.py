from google import genai
from google.genai import types
from app.ai.exceptions import AIProviderError
from app.ai.providers.prompts import SYSTEM_INSTRUCTION, build_prompt
from app.ai.schemas import EmailDecision
from app.core.config import Settings


class GeminiDecisionProvider:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.gemini_model
        self._client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def classify(self, email: str) -> EmailDecision:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=build_prompt(email),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=EmailDecision,
                    temperature=0,
            ),
        )

            return response.parsed

        except Exception as exc:
            raise AIProviderError("Failed to classify email.") from exc