import json
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from models.schemas import AnalysisResult
from utils.config import get_settings


class ReportGenerator:
    def __init__(self) -> None:
        self.report_dir = get_settings().report_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def json_report(self, scan_id: int, result: dict) -> Path:
        path = self.report_dir / f"scan-{scan_id}.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return path

    def pdf_report(self, scan_id: int, result: AnalysisResult) -> Path:
        path = self.report_dir / f"scan-{scan_id}.pdf"
        pdf = canvas.Canvas(str(path), pagesize=letter)
        width, height = letter
        y = height - 50
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(50, y, "CodeReviewAI Report")
        y -= 32
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"File: {result.filename}")
        y -= 18
        pdf.drawString(50, y, f"Quality: {result.scores.quality_score}/100 | Maintainability: {result.scores.maintainability_score}/100 | Complexity: {result.scores.cyclomatic_complexity}")
        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Top Issues")
        y -= 18
        pdf.setFont("Helvetica", 9)
        for issue in result.issues[:18]:
            if y < 80:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 9)
            text = f"L{issue.line} [{issue.severity}] {issue.rule}: {issue.message}"
            pdf.drawString(50, y, text[:110])
            y -= 14
        y -= 10
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "AI Suggestions")
        y -= 18
        pdf.setFont("Helvetica", 9)
        for suggestion in result.ai_suggestions[:8]:
            pdf.drawString(50, y, f"- {suggestion}"[:110])
            y -= 14
        pdf.save()
        return path
