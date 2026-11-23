"""
FastAPI Backend for Bulk Result Processing Web Application.
Provides RESTful APIs for portal validation, Excel parsing, bulk processing, and file exports.
"""
import os
import io
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from connectors.registry import get_registry
from engine.excel_parser import ExcelParser
from engine.processor import get_batch_processor

app = FastAPI(
    title="Open-Source Bulk Result Processing Engine",
    description="Universal multi-college bulk student result downloader and exporter",
    version="2.0.0"
)

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active uploaded files: upload_id -> {"filename": str, "bytes": bytes}
UPLOAD_CACHE: Dict[str, Dict[str, Any]] = {}

# Ensure base directories exist
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


# --- API Routes ---

@app.get("/api/portals")
def list_portals():
    """List all supported college/university portal connectors."""
    return {
        "success": True,
        "portals": registry.list_portals()
    }


@app.post("/api/portals/validate")
def validate_portal_url(req: ValidateUrlRequest):
    """Validate user entered result portal URL and identify compatible connector."""
    result = registry.validate_url(req.url)
    return result


@app.post("/api/upload")
async def upload_excel_file(file: UploadFile = File(...)):
    """Upload Excel file (.xlsx, .xls), detect columns, validate records, return preview."""
    filename = file.filename or "uploaded.xlsx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Only .xlsx and .xls Excel files are supported.")

    try:
        content = await file.read()
        parsed_data = ExcelParser.parse_file(content, filename)
        upload_id = str(uuid.uuid4())[:8]

        # Store in cache
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
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")


@app.post("/api/process/start")
def start_processing(req: ProcessStartRequest):
    """Start bulk student result processing."""
    file_info = UPLOAD_CACHE.get(req.upload_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="Uploaded file session expired or not found. Please re-upload.")

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

    # Create job
    job = processor.create_job(
        portal_url=req.portal_url,
        connector_id=req.connector_id,
        students=students,
        options=req.options
    )

    # Start background job
    processor.start_job(job.job_id)

    return {
        "success": True,
        "job_id": job.job_id,
        "total_records": job.total,
        "stats": stats
    }


@app.get("/api/process/status/{job_id}")
def get_process_status(job_id: str):
    """Get real-time status and logs for a processing job."""
    job = processor.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "success": True,
        "job": job.to_dict()
    }


@app.post("/api/process/retry/{job_id}/{enrollment}")
def retry_single_record(job_id: str, enrollment: str):
    """Retry a single failed student result extraction."""
    success = processor.retry_single(job_id, enrollment)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to retry record. Job may be actively running or not found.")
    return {"success": True, "message": f"Retry started for enrollment {enrollment}"}


@app.post("/api/process/retry-failed/{job_id}")
def retry_all_failed_records(job_id: str):
    """Retry all failed records in the job."""
    success = processor.retry_all_failed(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to retry. No failed records found or job is running.")
    return {"success": True, "message": "Bulk retry initiated for all failed records."}


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
    job = processor.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if file_type == "consolidated_excel":
        path = job.generated_files.get("consolidated_excel")
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Consolidated Excel not generated yet.")
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"consolidated_results_{job_id}.xlsx"
        )

    elif file_type == "subject_excel":
        path = job.generated_files.get("subject_excel")
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Subject-wise Excel not generated yet.")
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"subject_wise_results_{job_id}.xlsx"
        )

    elif file_type == "marksheets_zip":
        path = job.generated_files.get("marksheets_zip")
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Marksheets archive not available.")
        return FileResponse(
            path,
            media_type="application/zip",
            filename=f"marksheets_{job_id}.zip"
        )

    elif file_type == "complete_zip":
        path = job.generated_files.get("complete_zip")
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Complete package archive not available.")
        return FileResponse(
            path,
            media_type="application/zip",
            filename=f"complete_results_package_{job_id}.zip"
        )

    elif file_type == "pdf" and enrollment:
        res = job.results.get(enrollment)
        if not res or not res.pdf_path or not os.path.exists(res.pdf_path):
            raise HTTPException(status_code=404, detail=f"Marksheet file for {enrollment} not found.")
        ext = os.path.splitext(res.pdf_path)[1].lower()
        mime = "application/pdf" if ext == ".pdf" else "image/png"
        return FileResponse(
            res.pdf_path,
            media_type=mime,
            filename=f"marksheet_{enrollment}{ext}"
        )

    raise HTTPException(status_code=400, detail="Invalid file type requested.")


@app.delete("/api/cleanup/{job_id}")
def cleanup_job_files(job_id: str):
    """Delete temporary job files and free storage."""
    success = processor.cleanup_job(job_id)
    return {"success": success, "message": "Storage cleaned successfully."}


# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the single-page dashboard."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h3>Universal Bulk Result Processing App</h3><p>Frontend loading...</p>")


if __name__ == "__main__":
    import uvicorn
    print("Starting Universal Bulk Result Processing Server on http://127.0.0.1:8000 ...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
