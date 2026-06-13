from abc import ABC, abstractmethod
from typing import Any


class LLMService(ABC):
    @abstractmethod
    def analyze_sales_call(self, transcript: str) -> dict[str, Any]:
        raise NotImplementedError

