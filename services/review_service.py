from fastapi import HTTPException
from sqlalchemy.orm import Session

from analyzers.python_analyzer import PythonAnalyzer
from models.scan import Scan
from models.schemas import AnalysisResult
from services.ai_suggestions import SuggestionService


class ReviewService:
    def __init__(self) -> None:
        self.analyzers = {"python": PythonAnalyzer()}
        self.suggestions = SuggestionService()

    def analyze(self, code: str, filename: str, language: str = "python") -> AnalysisResult:
        analyzer = self.analyzers.get(language.lower())
        if not analyzer:
            raise HTTPException(status_code=400, detail=f"Language '{language}' is not supported yet.")
        result = analyzer.analyze(code, filename)
        return self.suggestions.enrich(result, code)

    def analyze_and_store(self, db: Session, user_id: int, code: str, filename: str, language: str = "python") -> tuple[AnalysisResult, Scan]:
        result = self.analyze(code, filename, language)
        scan = Scan(
            user_id=user_id,
            filename=filename,
            source_code=code,
            language=language,
            total_issues=len(result.issues),
            complexity=result.scores.cyclomatic_complexity,
            maintainability_score=result.scores.maintainability_score,
            readability_score=result.scores.readability_score,
            quality_score=result.scores.quality_score,
            result=result.model_dump(mode="json"),
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return result, scan
