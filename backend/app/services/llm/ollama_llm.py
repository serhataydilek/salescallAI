import json
import os
from http.client import HTTPException as HTTPClientException
from typing import Any
from urllib import error, request

from app.services.analysis.rubric import build_analysis_prompt
from app.services.llm.base import LLMService
from app.schemas import AnalysisBase


OLLAMA_JSON_CONTRACT = """
Ollama output contract:
- Return one valid JSON object only.
- Do not wrap the JSON in markdown fences.
- Do not include commentary before or after the JSON.
- Use every field from the provided schema.
- top_3_mistakes must contain exactly 3 strings.
- If the call is strong, top_3_mistakes must still contain 3 minor, useful improvement areas.
- missed_questions should contain 2 to 5 useful questions unless the transcript truly leaves no useful missed question.
- suggested_improvements must contain at least 3 strings.
- better_example_responses must contain at least 2 strings.
- short_summary must be specific to this transcript, not generic.
- Be strict with scores; do not reward missing discovery, weak objection handling, or no next step.
- Weak calls with vague product claims, no success metric, and no concrete next step should score in the weak range.
- Use evidence from the transcript. Do not make the report sound stronger than the actual sales behavior.
- Match the primary transcript language for all string values. Turkish transcript means Turkish report text; English transcript means English report text.
- Keep JSON keys in English. Do not translate field names.
"""


class OllamaLLMService(LLMService):
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    def analyze_sales_call(self, transcript: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": self._build_prompt(transcript),
            "stream": False,
            "format": AnalysisBase.model_json_schema(),
            "options": {"temperature": 0},
        }

        try:
            body = self._post_generate(payload)
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama returned HTTP {exc.code}. Check that model '{self.model}' is pulled. Details: {message}"
            ) from exc
        except (error.URLError, TimeoutError, ConnectionError, HTTPClientException) as exc:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. Start Ollama and verify OLLAMA_BASE_URL."
            ) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama returned an invalid API response, not JSON.") from exc

        raw_response = body.get("response", "")
        if not isinstance(raw_response, str) or not raw_response.strip():
            raise RuntimeError("Ollama returned an empty analysis response.")

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Ollama returned invalid JSON analysis. Try qwen2.5:7b or another model with stronger JSON output."
            ) from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("Ollama returned JSON, but it was not an object.")

        try:
            return AnalysisBase.model_validate(parsed).model_dump()
        except Exception as exc:
            raise RuntimeError(f"Ollama JSON did not match the SalesMirror analysis schema: {exc}") from exc

    def _post_generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        api_request = request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(api_request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))

    def _build_prompt(self, transcript: str) -> str:
        return f"{OLLAMA_JSON_CONTRACT}\n\n{build_analysis_prompt(transcript)}"
