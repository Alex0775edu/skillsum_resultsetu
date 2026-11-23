"""
FastAPI Backend for Bulk Academic Result Processing Platform.
Provides RESTful APIs for portal validation, Excel parsing, bulk processing,
file exports, and branding/privacy compliance.
"""
import os
import io
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from brand_config import (
    get_branding_context,
    MAX_UPLOAD_SIZE_BYTES,
    JOB_RETENTION_MINUTES,
    PROJECT_NAME,
    TAGLINE,
    VERSION
)
from connectors.registry import get_registry
from engine.excel_parser import ExcelParser
from engine.processor import get_batch_processor
from engine.security import validate_university_url, sanitize_job_id, safe_filename

app = FastAPI(
    title=PROJECT_NAME,
    description=TAGLINE,
    version=VERSION
)

# Enable CORS for local and intranet access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active uploaded files: upload_id -> {"filename": str, "bytes": bytes}
UPLOAD_CACHE: Dict[str, Dict[str, Any]] = {}

# Ensure directories exist
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_storage")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

processor = get_batch_processor()
registry = get_registry()


# --- Pydantic Request Models ---

class ValidateUrlRequest(BaseModel):
    url: str


class ProcessStartRequest(BaseModel):
    upload_id: str
    portal_url: str
    connector_id: str
    column_mapping: Dict[str, str]
    options: Dict[str, Any]


class DirectProcessStartRequest(BaseModel):
    portal_url: str
    connector_id: str
    students: List[Dict[str, Any]]
    options: Dict[str, Any]


# --- API Routes ---

@app.get("/api/config")
def get_config():
    """Return central branding, legal, and retention configuration."""
    return {
        "success": True,
        "config": get_branding_context()
    }


@app.get("/api/portals")
def list_portals():
    """List all supported college/university portal connectors."""
    return {
        "success": True,
        "portals": registry.list_portals()
    }


@app.post("/api/portals/validate")
def validate_portal_url_endpoint(req: ValidateUrlRequest):
    """Validate user entered result portal URL, check SSRF guards, and match connector."""
    result = registry.validate_url(req.url)
    return result


@app.post("/api/upload")
async def upload_excel_file(file: UploadFile = File(...)):
    """
    Fallback server-side upload: parse Excel file (.xlsx, .xls) in memory.
    Enforces maximum upload size limit (5MB).
    """
    filename = file.filename or "uploaded.xlsx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Only .xlsx and .xls Excel files are supported.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum permitted upload limit of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
        )

    try:
        parsed_data = ExcelParser.parse_file(content, filename)
        upload_id = str(uuid.uuid4())[:8]

        # Store in transient memory cache (not written to public static disk)
        UPLOAD_CACHE[upload_id] = {
            "filename": filename,
            "bytes": content
        }

        parsed_data["upload_id"] = upload_id
        return {
            "success": True,
            "data": parsed_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process Excel file: {str(e)}")


@app.post("/api/process/start_direct")
def start_processing_direct(req: DirectProcessStartRequest):
    """
    Privacy-First Primary Endpoint:
    Accepts student query data parsed directly inside the user's browser.
    The original Excel file is NEVER uploaded to the server!
    """
    is_safe, sec_msg = validate_university_url(req.portal_url)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"URL validation failed: {sec_msg}")

    if not req.students:
        raise HTTPException(status_code=400, detail="No student records provided for processing.")

    # Limit batch to reasonable size (e.g. 500 records per session)
    if len(req.students) > 1000:
        raise HTTPException(status_code=400, detail="Batch size exceeds limit of 1000 records per run.")

    # Sanitize student objects
    clean_students = []
    for s in req.students:
        enr = str(s.get("enrollment", "")).strip()
        if not enr:
            continue
        clean_students.append({
            "enrollment": enr,
            "dob": str(s.get("dob", "")).strip(),
            "name": str(s.get("name", "")).strip(),
            "father_name": str(s.get("father_name", "")).strip(),
            "branch": str(s.get("branch", "")).strip(),
        })

    if not clean_students:
        raise HTTPException(status_code=400, detail="No valid enrollment numbers found in submitted data.")

    job = processor.create_job(
        portal_url=req.portal_url,
        connector_id=req.connector_id,
        students=clean_students,
        options=req.options
    )
    processor.start_job(job.job_id)

    return {
        "success": True,
        "job_id": job.job_id,
        "total_records": job.total,
        "message": "Processing job initialized via client-local parsing."
    }


@app.post("/api/process/start")
def start_processing_server_upload(req: ProcessStartRequest):
    """Fallback bulk processing using transient uploaded file session."""
    is_safe, sec_msg = validate_university_url(req.portal_url)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"URL validation failed: {sec_msg}")

    file_info = UPLOAD_CACHE.get(req.upload_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File session expired or not found. Please re-upload.")

    try:
        students, stats = ExcelParser.extract_student_records(
            file_bytes=file_info["bytes"],
            filename=file_info["filename"],
            column_mapping=req.column_mapping,
            remove_duplicates=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not students:
        raise HTTPException(status_code=400, detail="No valid student records found after filtering.")

    job = processor.create_job(
        portal_url=req.portal_url,
        connector_id=req.connector_id,
        students=students,
        options=req.options
    )
    processor.start_job(job.job_id)

    # Clear cached bytes from memory after job creation
    UPLOAD_CACHE.pop(req.upload_id, None)

    return {
        "success": True,
        "job_id": job.job_id,
        "total_records": job.total,
        "stats": stats
    }


@app.get("/api/process/status/{job_id}")
def get_process_status(job_id: str):
    """Get real-time status and logs for a processing job."""
    try:
        clean_id = sanitize_job_id(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    job = processor.get_job(clean_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired under the 30-minute retention policy.")

    return {
        "success": True,
        "job": job.to_dict()
    }


@app.post("/api/process/retry/{job_id}/{enrollment}")
def retry_single_record(job_id: str, enrollment: str):
    """Retry a single failed student result extraction."""
    clean_id = sanitize_job_id(job_id)
    success = processor.retry_single(clean_id, enrollment)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to retry record. Job may be actively running or not found.")
    return {"success": True, "message": "Retry initiated."}


@app.post("/api/process/retry-failed/{job_id}")
def retry_all_failed_records(job_id: str):
    """Retry all failed records in the job."""
    clean_id = sanitize_job_id(job_id)
    success = processor.retry_all_failed(clean_id)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to retry. No failed records found or job is running.")
    return {"success": True, "message": "Bulk retry initiated."}


@app.get("/api/download/sample-template")
def download_sample_template():
    """Download the sample Excel template."""
    sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_students.xlsx")
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample template not found.")
    return FileResponse(
        sample_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="sample_students_template.xlsx"
    )


@app.get("/api/download/{job_id}/{file_type}")
def download_export_file(job_id: str, file_type: str, enrollment: Optional[str] = None):
    """Download generated Excel, ZIP, or individual marksheet PDF."""
    clean_id = sanitize_job_id(job_id)
    job = processor.get_job(clean_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job session expired or not found.")

    if file_type == "consolidated_excel":
        path = job.generated_files.get("consolidated_excel")
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Consolidated Excel not generated yet.")
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"consolidated_results_{clean_id}.xlsx"
        )

    elif file_type == "subject_excel":
        path = job.generated_files.get("subject_excel")
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Subject-wise Excel not generated yet.")
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"subject_wise_results_{clean_id}.xlsx"
        )

    elif file_type == "marksheets_zip":
        path = job.generated_files.get("marksheets_zip")
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Marksheets archive not available.")
        return FileResponse(
            path,
            media_type="application/zip",
            filename=f"marksheets_{clean_id}.zip"
        )

    elif file_type == "complete_zip":
        path = job.generated_files.get("complete_zip")
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Complete package archive not available.")
        return FileResponse(
            path,
            media_type="application/zip",
            filename=f"complete_results_package_{clean_id}.zip"
        )

    elif file_type == "pdf" and enrollment:
        res = job.results.get(enrollment)
        if not res or not res.pdf_path or not os.path.exists(res.pdf_path):
            raise HTTPException(status_code=404, detail="Requested marksheet document was not found.")
        ext = os.path.splitext(res.pdf_path)[1].lower()
        mime = "application/pdf" if ext == ".pdf" else "image/png"
        return FileResponse(
            res.pdf_path,
            media_type=mime,
            filename=f"marksheet_{safe_filename(enrollment)}{ext}"
        )

    raise HTTPException(status_code=400, detail="Invalid export artifact requested.")


@app.delete("/api/cleanup/{job_id}")
def cleanup_job_files(job_id: str):
    """Explicitly delete temporary job files and release storage immediately."""
    clean_id = sanitize_job_id(job_id)
    success = processor.cleanup_job(clean_id)
    return {"success": success, "message": "Storage cleaned successfully."}


# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _serve_spa():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h3>Academic Result Processing App</h3>")


# Support direct URLs for all 12 navigation pages by routing to the responsive SPA shell
@app.get("/", response_class=HTMLResponse)
@app.get("/process", response_class=HTMLResponse)
@app.get("/how-it-works", response_class=HTMLResponse)
@app.get("/universities", response_class=HTMLResponse)
@app.get("/faq", response_class=HTMLResponse)
@app.get("/privacy", response_class=HTMLResponse)
@app.get("/terms", response_class=HTMLResponse)
@app.get("/disclaimer", response_class=HTMLResponse)
@app.get("/data-handling", response_class=HTMLResponse)
@app.get("/copyright", response_class=HTMLResponse)
@app.get("/contact", response_class=HTMLResponse)
@app.get("/license", response_class=HTMLResponse)
def index_pages():
    return _serve_spa()


if __name__ == "__main__":
    import uvicorn
    print(f"Starting {PROJECT_NAME} on http://127.0.0.1:8000 ...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
