from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionMetadata:
    model_name: str
    latency_ms: float
    prompt_version: str
    fallback_used: bool
    confidence: float