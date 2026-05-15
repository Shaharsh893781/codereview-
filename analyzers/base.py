from abc import ABC, abstractmethod

from models.schemas import AnalysisResult


class CodeAnalyzer(ABC):
    language: str

    @abstractmethod
    def analyze(self, code: str, filename: str) -> AnalysisResult:
        raise NotImplementedError
