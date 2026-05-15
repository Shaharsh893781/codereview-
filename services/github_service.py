from models.schemas import AnalysisResult
from services.review_service import ReviewService


class GitHubSimulationService:
    def __init__(self) -> None:
        self.reviewer = ReviewService()

    def simulate_pull_request(self, files: dict[str, str]) -> dict:
        file_reviews: list[AnalysisResult] = []
        for filename, code in files.items():
            if filename.endswith(".py"):
                file_reviews.append(self.reviewer.analyze(code, filename))
        total_issues = sum(len(review.issues) for review in file_reviews)
        blocking = sum(1 for review in file_reviews for issue in review.issues if issue.severity == "critical")
        return {
            "summary": "changes_requested" if blocking else "approved_with_comments",
            "files_reviewed": len(file_reviews),
            "total_issues": total_issues,
            "blocking_issues": blocking,
            "reviews": [review.model_dump(mode="json") for review in file_reviews],
        }
