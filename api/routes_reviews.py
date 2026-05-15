from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models.scan import Scan
from models.schemas import AnalysisResult, CodeAnalyzeRequest, ScanSummary
from models.user import User
from reports.report_generator import ReportGenerator
from services.github_service import GitHubSimulationService
from services.review_service import ReviewService


router = APIRouter(prefix="/api", tags=["reviews"])
review_service = ReviewService()
reports = ReportGenerator()


@router.post("/analyze", response_model=AnalysisResult)
def analyze_code(payload: CodeAnalyzeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> AnalysisResult:
    result, _scan = review_service.analyze_and_store(db, user.id, payload.code, payload.filename, payload.language)
    return result


@router.post("/upload", response_model=AnalysisResult)
async def upload_code(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> AnalysisResult:
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only Python files are supported in this release.")
    code = (await file.read()).decode("utf-8")
    result, _scan = review_service.analyze_and_store(db, user.id, code, file.filename, "python")
    return result


@router.get("/scans", response_model=list[ScanSummary])
def scan_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[ScanSummary]:
    return db.query(Scan).filter(Scan.user_id == user.id).order_by(Scan.created_at.desc()).limit(50).all()


@router.get("/scans/{scan_id}", response_model=AnalysisResult)
def scan_detail(scan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> AnalysisResult:
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return AnalysisResult.model_validate(scan.result)


@router.get("/scans/{scan_id}/report/{kind}")
def download_report(scan_id: int, kind: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    result = AnalysisResult.model_validate(scan.result)
    if kind == "json":
        path = reports.json_report(scan.id, scan.result)
        return FileResponse(path, media_type="application/json", filename=path.name)
    if kind == "pdf":
        path = reports.pdf_report(scan.id, result)
        return FileResponse(path, media_type="application/pdf", filename=path.name)
    raise HTTPException(status_code=400, detail="Report kind must be 'json' or 'pdf'.")


@router.post("/pull-request/simulate")
def simulate_pull_request(files: dict[str, str], user: User = Depends(get_current_user)) -> dict:
    return GitHubSimulationService().simulate_pull_request(files)
