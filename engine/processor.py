"""
Bulk Result Processor Orchestrator.
Manages background job queues, privacy-conscious logging, automated TTL retention,
and export generation.
"""
import os
import shutil
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from connectors.base import BaseConnector, StudentResult
from connectors.registry import get_registry
from brand_config import JOB_RETENTION_MINUTES
from engine.security import sanitize_job_id
from .exporter import ResultExporter


class ProcessingJob:
    """Represents a bulk processing session."""

    def __init__(
        self,
        job_id: str,
        portal_url: str,
        connector_id: str,
        students: List[Dict[str, Any]],
        options: Dict[str, Any],
        storage_dir: str
    ):
        self.job_id = sanitize_job_id(job_id)
        self.portal_url = portal_url
        self.connector_id = connector_id
        self.students = students
        self.options = options
        self.storage_dir = storage_dir

        self.pdf_dir = os.path.join(storage_dir, "marksheets")
        self.exports_dir = os.path.join(storage_dir, "exports")
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)

        self.status = "queued"  # queued, running, completed, cancelled, expired
        self.created_at = time.time()
        self.total = len(students)
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.current_display = ""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.logs: List[str] = []

        # Store results keyed by enrollment
        self.results: Dict[str, StudentResult] = {}
        for s in students:
            enr = s.get("enrollment", "")
            self.results[enr] = StudentResult(
                enrollment=enr,
                student_name=s.get("name", ""),
                status="Pending"
            )

        self.generated_files = {
            "consolidated_excel": None,
            "subject_excel": None,
            "marksheets_zip": None,
            "complete_zip": None
        }

    def add_log(self, message: str) -> None:
        """Add timestamped privacy-safe activity log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    def get_progress_percent(self) -> float:
        if self.total == 0:
            return 100.0
        return round((self.processed / self.total) * 100, 1)

    def get_elapsed_seconds(self) -> float:
        if not self.start_time:
            return 0.0
        end = self.end_time or time.time()
        return round(end - self.start_time, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "portal_url": self.portal_url,
            "connector_id": self.connector_id,
            "status": self.status,
            "total": self.total,
            "processed": self.processed,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "percent": self.get_progress_percent(),
            "elapsed_seconds": self.get_elapsed_seconds(),
            "current_display": self.current_display,
            "recent_logs": self.logs[-15:],
            "results": [r.to_dict() for r in self.results.values()],
            "files": {
                k: bool(v and os.path.exists(v)) for k, v in self.generated_files.items()
            }
        }


class BatchProcessor:
    """Manages bulk processing jobs, worker threads, and automatic temporary file cleanup."""

    def __init__(self, base_storage_dir: str = "temp_storage"):
        self.base_storage_dir = base_storage_dir
        os.makedirs(self.base_storage_dir, exist_ok=True)
        self.jobs: Dict[str, ProcessingJob] = {}
        self._lock = threading.Lock()

        # Start background automatic TTL cleaner
        self._cleaner_thread = threading.Thread(target=self._retention_cleaner_loop, daemon=True)
        self._cleaner_thread.start()

    def _retention_cleaner_loop(self) -> None:
        """Periodically purge temporary job files older than JOB_RETENTION_MINUTES."""
        retention_seconds = JOB_RETENTION_MINUTES * 60
        while True:
            time.sleep(60)  # Check every minute
            now = time.time()
            expired_ids = []
            with self._lock:
                for jid, job in self.jobs.items():
                    if (now - job.created_at) > retention_seconds:
                        expired_ids.append(jid)

            for jid in expired_ids:
                self.cleanup_job(jid)

    def create_job(
        self,
        portal_url: str,
        connector_id: str,
        students: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> ProcessingJob:
        raw_id = str(uuid.uuid4())[:8]
        job_id = sanitize_job_id(raw_id)
        job_dir = os.path.join(self.base_storage_dir, job_id)
        job = ProcessingJob(job_id, portal_url, connector_id, students, options, job_dir)

        with self._lock:
            self.jobs[job_id] = job

        return job

    def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        try:
            clean_id = sanitize_job_id(job_id)
        except Exception:
            return None
        with self._lock:
            return self.jobs.get(clean_id)

    def start_job(self, job_id: str) -> bool:
        job = self.get_job(job_id)
        if not job or job.status == "running":
            return False

        worker_thread = threading.Thread(
            target=self._run_job_worker,
            args=(job,),
            daemon=True
        )
        worker_thread.start()
        return True

    @staticmethod
    def _mask_id(identifier: str) -> str:
        """Privacy mask for student enrollment numbers in activity logs."""
        clean = str(identifier).strip()
        if len(clean) <= 4:
            return f"***{clean}"
        return f"...{clean[-4:]}"

    def retry_single(self, job_id: str, enrollment: str) -> bool:
        """Retry processing for a single failed student."""
        job = self.get_job(job_id)
        if not job or job.status == "running":
            return False

        student_data = next((s for s in job.students if s.get("enrollment") == enrollment), None)
        if not student_data:
            return False

        def _retry_worker():
            job.status = "running"
            masked = self._mask_id(enrollment)
            job.add_log(f"Retrying single student record ({masked})")
            registry = get_registry()
            connector = registry.get_by_id(job.connector_id)
            if not connector:
                job.add_log(f"Connector '{job.connector_id}' not found.")
                job.status = "completed"
                return

            try:
                connector.initialize()
                retry_options = dict(job.options)
                retry_options["force_download"] = True

                res = connector.fetch_result(
                    job.portal_url, student_data, retry_options, job.pdf_dir
                )

                old_res = job.results.get(enrollment)
                if old_res and old_res.status == "Failed":
                    job.failed = max(0, job.failed - 1)

                job.results[enrollment] = res
                if res.status in ("Success", "Cached"):
                    job.successful += 1
                    job.add_log(f"Retry succeeded for record ({masked})")
                else:
                    job.failed += 1
                    job.add_log(f"Retry failed for record ({masked}): {res.error_message}")

                self._generate_exports(job)
            except Exception as e:
                job.add_log(f"Error during retry: {str(e)}")
            finally:
                connector.cleanup()
                job.status = "completed"

        threading.Thread(target=_retry_worker, daemon=True).start()
        return True

    def retry_all_failed(self, job_id: str) -> bool:
        """Retry all failed records in the job."""
        job = self.get_job(job_id)
        if not job or job.status == "running":
            return False

        failed_enrollments = [
            enr for enr, r in job.results.items() if r.status == "Failed"
        ]
        if not failed_enrollments:
            return False

        failed_students = [
            s for s in job.students if s.get("enrollment") in failed_enrollments
        ]

        def _retry_all_worker():
            job.status = "running"
            job.add_log(f"Retrying all {len(failed_students)} failed records...")
            registry = get_registry()
            connector = registry.get_by_id(job.connector_id)
            if not connector:
                job.status = "completed"
                return

            try:
                connector.initialize()
                retry_options = dict(job.options)
                retry_options["force_download"] = True

                for idx, s in enumerate(failed_students, 1):
                    enr = s.get("enrollment", "")
                    masked = self._mask_id(enr)
                    job.current_display = f"Retry [{idx}/{len(failed_students)}] ({masked})"
                    job.add_log(f"Retrying record [{idx}/{len(failed_students)}] ({masked})...")

                    res = connector.fetch_result(
                        job.portal_url, s, retry_options, job.pdf_dir
                    )

                    old_res = job.results.get(enr)
                    if old_res and old_res.status == "Failed":
                        job.failed = max(0, job.failed - 1)

                    job.results[enr] = res
                    if res.status in ("Success", "Cached"):
                        job.successful += 1
                        job.add_log(f"Retry success for record ({masked})")
                    else:
                        job.failed += 1
                        job.add_log(f"Retry unsuccessful for record ({masked}): {res.error_message}")

                    time.sleep(0.3)

                self._generate_exports(job)
            except Exception as e:
                job.add_log(f"Exception during bulk retry: {str(e)}")
            finally:
                connector.cleanup()
                job.current_display = ""
                job.status = "completed"
                job.add_log("Bulk retry operation completed.")

        threading.Thread(target=_retry_all_worker, daemon=True).start()
        return True

    def _run_job_worker(self, job: ProcessingJob) -> None:
        """Main bulk processing loop with privacy-safe activity logging."""
        job.status = "running"
        job.start_time = time.time()
        job.add_log(f"Bulk processing started. Total student records: {job.total}")

        registry = get_registry()
        connector = registry.get_by_id(job.connector_id)
        if not connector:
            job.status = "failed"
            job.add_log(f"ERROR: Connector '{job.connector_id}' not found in registry.")
            return

        try:
            connector.initialize()
            job.add_log(f"Connected to portal handler: {connector.name}")

            for idx, student in enumerate(job.students, 1):
                enrollment = student.get("enrollment", "")
                masked = self._mask_id(enrollment)
                job.current_display = f"Record [{idx}/{job.total}] ({masked})"
                job.add_log(f"Processing record [{idx}/{job.total}] ({masked})...")

                try:
                    res = connector.fetch_result(
                        portal_url=job.portal_url,
                        student_data=student,
                        options=job.options,
                        output_dir=job.pdf_dir
                    )

                    job.results[enrollment] = res
                    job.processed += 1

                    if res.status in ("Success", "Cached"):
                        job.successful += 1
                        job.add_log(f"Record [{idx}/{job.total}] extracted successfully")
                    elif res.status == "Skipped":
                        job.skipped += 1
                        job.add_log(f"Record [{idx}/{job.total}] skipped: {res.error_message}")
                    else:
                        job.failed += 1
                        job.add_log(f"Record [{idx}/{job.total}] failed: {res.error_message}")

                except Exception as ex:
                    job.processed += 1
                    job.failed += 1
                    err_res = StudentResult(
                        enrollment=enrollment,
                        student_name=student.get("name", ""),
                        status="Failed",
                        error_message=f"Processing exception: {str(ex)[:100]}"
                    )
                    job.results[enrollment] = err_res
                    job.add_log(f"Exception on record [{idx}/{job.total}]: {str(ex)[:80]}")

                # Polite delay between requests to respect university servers
                time.sleep(0.4)

        except Exception as e:
            job.add_log(f"Fatal job error: {str(e)}")
        finally:
            connector.cleanup()
            job.end_time = time.time()
            job.current_display = ""
            job.status = "completed"
            job.add_log(
                f"Job finished in {job.get_elapsed_seconds()}s. "
                f"Success: {job.successful}, Failed: {job.failed}, Skipped: {job.skipped}"
            )

            # Generate export files automatically
            try:
                self._generate_exports(job)
                job.add_log("Export packages generated successfully.")
            except Exception as exp_err:
                job.add_log(f"Export generation notice: {str(exp_err)}")

    def _generate_exports(self, job: ProcessingJob) -> None:
        """Create Excel sheets, PDF marksheets ZIP, and Complete Package ZIP."""
        results_list = list(job.results.values())
        if not results_list:
            return

        # 1. Consolidated Excel
        cons_path = os.path.join(job.exports_dir, "consolidated_results.xlsx")
        ResultExporter.generate_consolidated_excel(results_list, job.options, cons_path)
        job.generated_files["consolidated_excel"] = cons_path

        # 2. Subject-wise Excel
        subj_path = os.path.join(job.exports_dir, "subject_wise_results.xlsx")
        ResultExporter.generate_subject_wise_excel(results_list, job.options, subj_path)
        job.generated_files["subject_excel"] = subj_path

        # Gather PDF marksheets
        pdf_files = [r.pdf_path for r in results_list if r.pdf_path and os.path.exists(r.pdf_path)]

        # 3. Marksheets ZIP
        if pdf_files:
            zip_marksheets = os.path.join(job.exports_dir, "marksheets_archive.zip")
            ResultExporter.create_marksheets_zip(pdf_files, zip_marksheets)
            job.generated_files["marksheets_zip"] = zip_marksheets

        # 4. Complete Package ZIP
        summary_info = {
            "job_id": job.job_id,
            "portal_url": job.portal_url,
            "connector_id": job.connector_id,
            "total_records": job.total,
            "successful": job.successful,
            "failed": job.failed,
            "skipped": job.skipped,
            "duration_seconds": job.get_elapsed_seconds(),
            "export_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        zip_complete = os.path.join(job.exports_dir, "complete_result_package.zip")
        ResultExporter.create_complete_package_zip(
            consolidated_excel=cons_path,
            subject_excel=subj_path,
            pdf_files=pdf_files,
            summary_data=summary_info,
            zip_filepath=zip_complete
        )
        job.generated_files["complete_zip"] = zip_complete

    def cleanup_job(self, job_id: str) -> bool:
        """Delete temporary files for a completed or expired job."""
        try:
            clean_id = sanitize_job_id(job_id)
        except Exception:
            return False
        with self._lock:
            job = self.jobs.pop(clean_id, None)
            if job and os.path.exists(job.storage_dir):
                shutil.rmtree(job.storage_dir, ignore_errors=True)
                return True
        return False


_processor_instance: Optional[BatchProcessor] = None


def get_batch_processor() -> BatchProcessor:
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = BatchProcessor()
    return _processor_instance
