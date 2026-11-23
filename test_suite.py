"""
Comprehensive Test Suite for Bulk Result Processing Web Application.
Tests connectors, Excel parsing, bulk processing engine, export generation, and API endpoints.
"""
import os
import io
import time
import unittest
import pandas as pd
from fastapi.testclient import TestClient

from app import app
from connectors.registry import get_registry
from engine.excel_parser import ExcelParser
from engine.exporter import ResultExporter
from engine.processor import get_batch_processor
from connectors.base import StudentResult, SubjectMarks


class TestResultProcessor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_temp")
        os.makedirs(cls.test_dir, exist_ok=True)

    def test_01_connector_registry(self):
        """Test portal URL matching and validation."""
        registry = get_registry()
        
        # Test BTEUP match
        res_bteup = registry.validate_url("https://result.bteexam.com/even/main/rollno.aspx")
        self.assertTrue(res_bteup["supported"])
        self.assertEqual(res_bteup["connector_id"], "bteup")

        # Test Demo University match
        res_demo = registry.validate_url("https://results.university.edu/semester/exam")
        self.assertTrue(res_demo["supported"])
        self.assertEqual(res_demo["connector_id"], "demo_university")

        # Test Unsupported URL
        res_unknown = registry.validate_url("https://random-unknown-college.org/results")
        self.assertTrue(res_unknown["valid"])
        self.assertFalse(res_unknown["supported"])
        self.assertIn("No compatible connector found", res_unknown["message"])

    def test_02_excel_parsing_and_mapping(self):
        """Test Excel upload parser, column auto-detection, and deduplication."""
        test_df = pd.DataFrame([
            {"Roll_No": "21001", "DOB": "10/01/2003", "Student_Name": "Alice"},
            {"Roll_No": "21002", "DOB": "12/02/2003", "Student_Name": "Bob"},
            {"Roll_No": "21001", "DOB": "10/01/2003", "Student_Name": "Alice Duplicate"},
            {"Roll_No": "", "DOB": "14/03/2003", "Student_Name": "Empty Roll"},
        ])
        buffer = io.BytesIO()
        test_df.to_excel(buffer, index=False)
        excel_bytes = buffer.getvalue()

        parsed = ExcelParser.parse_file(excel_bytes, "test.xlsx")
        self.assertEqual(parsed["total_rows"], 4)
        self.assertEqual(parsed["detected_mapping"]["enrollment"], "Roll_No")
        self.assertEqual(parsed["detected_mapping"]["dob"], "DOB")
        self.assertEqual(parsed["detected_mapping"]["name"], "Student_Name")
        self.assertEqual(parsed["duplicate_count"], 1)
        self.assertEqual(parsed["empty_count"], 1)
        self.assertEqual(parsed["valid_count"], 2)

        # Extract records with deduplication
        records, stats = ExcelParser.extract_student_records(
            file_bytes=excel_bytes,
            filename="test.xlsx",
            column_mapping={"enrollment": "Roll_No", "dob": "DOB", "name": "Student_Name"},
            remove_duplicates=True
        )
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["enrollment"], "21001")
        self.assertEqual(records[1]["enrollment"], "21002")

    def test_03_export_excel_and_zip(self):
        """Test dynamic consolidated Excel, subject sheets, and ZIP creation."""
        results = [
            StudentResult(
                enrollment="E001",
                student_name="Test Student 1",
                branch="Computer Science",
                total_obtained=380.0,
                total_max=500.0,
                overall_percentage=76.0,
                result_status="PASS",
                division="First Division",
                status="Success",
                subjects=[
                    SubjectMarks(code="CS101", name="Algorithms", theory_max=100, theory_obtained=82, total_max=100, total_obtained=82, percentage=82.0, status="PASS"),
                    SubjectMarks(code="CS102", name="Networks", theory_max=100, theory_obtained=78, total_max=100, total_obtained=78, percentage=78.0, status="PASS"),
                ]
            ),
            StudentResult(
                enrollment="E002",
                student_name="Test Student 2",
                branch="Computer Science",
                total_obtained=240.0,
                total_max=500.0,
                overall_percentage=48.0,
                result_status="FAIL",
                division="Fail",
                status="Success",
                subjects=[
                    SubjectMarks(code="CS101", name="Algorithms", theory_max=100, theory_obtained=30, total_max=100, total_obtained=30, percentage=30.0, status="FAIL"),
                    SubjectMarks(code="CS102", name="Networks", theory_max=100, theory_obtained=55, total_max=100, total_obtained=55, percentage=55.0, status="PASS"),
                ]
            )
        ]

        # Consolidated Excel
        cons_path = os.path.join(self.test_dir, "test_consolidated.xlsx")
        ResultExporter.generate_consolidated_excel(results, {"include_all_subjects": True, "include_totals": True, "include_percentage": True, "include_status": True}, cons_path)
        self.assertTrue(os.path.exists(cons_path))
        self.assertGreater(os.path.getsize(cons_path), 1000)

        # Subject-wise Excel
        subj_path = os.path.join(self.test_dir, "test_subject_wise.xlsx")
        ResultExporter.generate_subject_wise_excel(results, {}, subj_path)
        self.assertTrue(os.path.exists(subj_path))
        self.assertGreater(os.path.getsize(subj_path), 1000)

        # ZIP Package
        zip_path = os.path.join(self.test_dir, "test_package.zip")
        ResultExporter.create_complete_package_zip(
            consolidated_excel=cons_path,
            subject_excel=subj_path,
            pdf_files=[],
            summary_data={"test": True, "total": 2},
            zip_filepath=zip_path
        )
        self.assertTrue(os.path.exists(zip_path))
        self.assertGreater(os.path.getsize(zip_path), 500)

    def test_04_api_end_to_end_flow(self):
        """Test complete API workflow from upload to processing and downloading."""
        # 1. Upload sample template
        with open("sample_students.xlsx", "rb") as f:
            resp = self.client.post("/api/upload", files={"file": ("sample_students.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        upload_id = data["data"]["upload_id"]
        detected_col = data["data"]["detected_mapping"]["enrollment"]

        # 2. Start Bulk Processing using Demo University connector
        start_payload = {
            "upload_id": upload_id,
            "portal_url": "https://results.university.edu/semester/exam",
            "connector_id": "demo_university",
            "column_mapping": {
                "enrollment": detected_col,
                "dob": data["data"]["detected_mapping"]["dob"] or "",
                "name": data["data"]["detected_mapping"]["name"] or ""
            },
            "options": {
                "include_all_subjects": True,
                "include_theory": True,
                "include_practical": True,
                "include_internal": True,
                "include_subject_pct": True,
                "include_totals": True,
                "include_percentage": True,
                "include_status": True,
                "download_pdf": True,
                "force_download": False
            }
        }
        resp = self.client.post("/api/process/start", json=start_payload)
        self.assertEqual(resp.status_code, 200)
        job_id = resp.json()["job_id"]

        # 3. Wait for background processing to finish
        for _ in range(15):
            time.sleep(0.5)
            status_resp = self.client.get(f"/api/process/status/{job_id}")
            self.assertEqual(status_resp.status_code, 200)
            job_data = status_resp.json()["job"]
            if job_data["status"] in ("completed", "failed"):
                break

        self.assertEqual(job_data["status"], "completed")
        self.assertGreater(job_data["processed"], 0)
        self.assertGreater(job_data["successful"], 0)

        # 4. Verify Download endpoints
        res_excel = self.client.get(f"/api/download/{job_id}/consolidated_excel")
        self.assertEqual(res_excel.status_code, 200)

        res_subj = self.client.get(f"/api/download/{job_id}/subject_excel")
        self.assertEqual(res_subj.status_code, 200)

        res_zip = self.client.get(f"/api/download/{job_id}/complete_zip")
        self.assertEqual(res_zip.status_code, 200)


if __name__ == "__main__":
    unittest.main()
