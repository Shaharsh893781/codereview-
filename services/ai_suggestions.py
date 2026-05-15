from models.schemas import AnalysisResult
from utils.config import get_settings


class SuggestionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def enrich(self, result: AnalysisResult, code: str) -> AnalysisResult:
        result.ai_suggestions = self._local_suggestions(result)
        return result

    def _local_suggestions(self, result: AnalysisResult) -> list[str]:
        rules = {issue.rule for issue in result.issues}
        suggestions = []
        if "high-complexity" in rules or "deep-nesting" in rules:
            suggestions.append("Prioritize flattening control flow with guard clauses and smaller pure functions.")
        if "duplicate-logic" in rules:
            suggestions.append("Create shared helpers for repeated branches so future fixes happen in one place.")
        if "security-risk" in rules:
            suggestions.append("Remove dynamic execution paths and validate all untrusted input at the boundary.")
        if "too-many-parameters" in rules:
            suggestions.append("Group related parameters into typed request objects or dataclasses.")
        if "unused-variable" in rules:
            suggestions.append("Clean unused assignments before deeper refactors; they often reveal stale logic.")
        if not suggestions:
            suggestions.append("The code is in good shape. Add focused tests around edge cases to preserve quality.")
        suggestions.append(f"Current quality score is {result.scores.quality_score}/100; use the issue list as the next refactor backlog.")
        return suggestions
