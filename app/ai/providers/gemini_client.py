from google import genai

from app.core.config import Settings


def build_gemini_client(
    settings: Settings,
) -> genai.Client:
    backend = settings.gemini_backend.strip().lower()

    if backend == "api_key":
        return genai.Client(
            api_key=settings.gemini_api_key,
        )

    if backend == "vertex":
        if not settings.google_cloud_project:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT is required "
                "when GEMINI_BACKEND=vertex."
            )

        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    raise ValueError(
        "Unsupported GEMINI_BACKEND: "
        f"{settings.gemini_backend!r}. "
        "Expected 'api_key' or 'vertex'."
    )
