import time
from typing import Dict, Any, Optional, Generator
from google import genai
from src.core.llm_provider import LLMProvider

class GoogleProvider(LLMProvider):
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None
    ):
        super().__init__(model_name, api_key)

        self.client = genai.Client(
            api_key=self.api_key
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:

        start_time = time.time()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt
        )

        end_time = time.time()

        latency_ms = int((end_time - start_time) * 1000)

        content = response.text

        usage = {}

        # Một số phiên bản Gemini có usage_metadata
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": getattr(
                    response.usage_metadata,
                    "prompt_token_count",
                    None
                ),
                "completion_tokens": getattr(
                    response.usage_metadata,
                    "candidates_token_count",
                    None
                ),
                "total_tokens": getattr(
                    response.usage_metadata,
                    "total_token_count",
                    None
                )
            }

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "google"
        }

    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:

        full_prompt = prompt

        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"

        stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=full_prompt
        )

        for chunk in stream:
            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text