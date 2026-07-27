from google import genai
from google.genai import types

from app.ai.providers.prompts import EMAIL_DECISION_SYSTEM_PROMPT
from app.ai.schemas import EmailDecision
from app.core.config import Settings


class GeminiDecisionProvider:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.gemini_model
        self._client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def classify(self, email: str) -> EmailDecision:
        response = self._client.models.generate_content(
            model=self._model,
            contents=email,
            config=types.GenerateContentConfig(
                system_instruction=EMAIL_DECISION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=EmailDecision,
        ),
    )

        return response.parsed