"""
Comprehensive Test Suite for Bulk Result Processing Platform.
Tests connectors, Excel parsing, bulk processing engine, export generation,
SSRF guards, path traversal sanitization, and API endpoints.
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
from engine.security import validate_university_url, sanitize_job_id
from engine.analytics import ResultVerifier, AcademicAnalytics
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

        # Test Unsupported external URL
        res_unknown = registry.validate_url("https://example.com/results")
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

    def test_05_ssrf_and_security_guards(self):
        """Verify SSRF protection on internal/loopback URLs and path traversal guards."""
        # 1. Loopback URL rejection
        safe, msg = validate_university_url("http://127.0.0.1:8080/admin")
        self.assertFalse(safe)
        self.assertIn("loopback", msg.lower())

        safe_local, _ = validate_university_url("http://localhost:5000/api")
        self.assertFalse(safe_local)

        # 2. Metadata IP rejection
        safe_meta, _ = validate_university_url("http://169.254.169.254/latest/meta-data")
        self.assertFalse(safe_meta)

        # 3. Non-http scheme rejection
        safe_file, _ = validate_university_url("file:///etc/passwd")
        self.assertFalse(safe_file)

        # 4. Path traversal on job_id
        with self.assertRaises(ValueError):
            sanitize_job_id("../../etc/passwd")

        with self.assertRaises(ValueError):
            sanitize_job_id("")

        self.assertEqual(sanitize_job_id("abc123_-"), "abc123_-")

    def test_06_direct_client_parsed_bulk_processing(self):
        """Test privacy-first /api/process/start_direct endpoint."""
        direct_payload = {
            "portal_url": "https://results.university.edu/semester/exam",
            "connector_id": "demo_university",
            "students": [
                {"enrollment": "DIR2001", "name": "Direct Student 1", "dob": "01/01/2003"},
                {"enrollment": "DIR2002", "name": "Direct Student 2", "dob": "02/02/2003"},
            ],
            "options": {
                "include_all_subjects": True,
                "include_totals": True,
                "download_pdf": True
            }
        }
        resp = self.client.post("/api/process/start_direct", json=direct_payload)
        self.assertEqual(resp.status_code, 200)
        job_id = resp.json()["job_id"]

        for _ in range(15):
            time.sleep(0.5)
            status_resp = self.client.get(f"/api/process/status/{job_id}")
            job_data = status_resp.json()["job"]
            if job_data["status"] in ("completed", "failed"):
                break

        self.assertEqual(job_data["status"], "completed")
        self.assertEqual(job_data["processed"], 2)
        self.assertEqual(job_data["successful"], 2)

    def test_07_config_branding_endpoint(self):
        """Verify centralized branding context returned by /api/config."""
        resp = self.client.get("/api/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["config"]
        self.assertEqual(data["owner_name"], "SkillSum Innovations")
        self.assertEqual(data["project_name"], "SkillSum ResultSetu")
        self.assertEqual(data["project_slug"], "skillsum-resultsetu")
        self.assertEqual(data["support_email"], "[SUPPORT_EMAIL_PLACEHOLDER]")
        self.assertEqual(data["analytics_enabled"], False)

    def test_08_file_size_limit_rejection(self):
        """Verify files larger than 5MB are rejected with 413."""
        oversized_data = b"0" * (6 * 1024 * 1024)  # 6 MB
        resp = self.client.post(
            "/api/upload",
            files={"file": ("huge.xlsx", io.BytesIO(oversized_data), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        self.assertEqual(resp.status_code, 413)

    def test_09_result_verifier_integrity(self):
        """Test verification engine checks for marks boundaries, negative marks, and missing marks."""
        # 1. Invalid: obtained exceeds max
        bad_student = StudentResult(
            enrollment="ERR001",
            student_name="Exceed Marks",
            status="Success",
            total_obtained=650.0,
            total_max=500.0,
            overall_percentage=130.0,
            subjects=[
                SubjectMarks(code="CS1", name="Math", theory_max=100, theory_obtained=110)
            ]
        )
        flags = ResultVerifier.verify(bad_student)
        self.assertTrue(any("exceeds maximum" in f.lower() for f in flags))
        self.assertTrue(any("theory obtained" in f.lower() for f in flags))

        # 2. Negative marks
        neg_student = StudentResult(
            enrollment="ERR002",
            student_name="Negative Marks",
            status="Success",
            total_obtained=-10.0,
            total_max=500.0,
            subjects=[
                SubjectMarks(code="CS2", name="Physics", practical_max=50, practical_obtained=-5)
            ]
        )
        neg_flags = ResultVerifier.verify(neg_student)
        self.assertTrue(any("negative total marks" in f.lower() for f in neg_flags))
        self.assertTrue(any("negative practical marks" in f.lower() for f in neg_flags))

        # 3. Missing / unpublished marks
        unpub_student = StudentResult(
            enrollment="ERR003",
            student_name="Unpublished Marks",
            status="Success",
            total_obtained=200.0,
            total_max=500.0,
            overall_percentage=40.0,
            subjects=[
                SubjectMarks(code="CS3", name="Lab", theory_max=None, theory_obtained=None, practical_max=None, practical_obtained=None, total_obtained=None)
            ]
        )
        unpub_flags = ResultVerifier.verify(unpub_student)
        self.assertTrue(any("unavailable or not published" in f.lower() for f in unpub_flags))

        # 4. Valid student should have zero flags
        valid_student = StudentResult(
            enrollment="OK001",
            student_name="Valid Student",
            status="Success",
            total_obtained=400.0,
            total_max=500.0,
            overall_percentage=80.0,
            subjects=[
                SubjectMarks(code="CS1", name="Math", theory_max=100, theory_obtained=80, total_max=100, total_obtained=80)
            ]
        )
        valid_flags = ResultVerifier.verify(valid_student)
        self.assertEqual(len(valid_flags), 0)

    def test_10_academic_analytics(self):
        """Test tied competition ranking (1224) and cohort statistics."""
        s1 = StudentResult(enrollment="S1", student_name="Topper 1", status="Success", overall_percentage=90.0, total_obtained=450.0, total_max=500.0, result_status="PASS")
        s2 = StudentResult(enrollment="S2", student_name="Topper 2 (Tied)", status="Success", overall_percentage=90.0, total_obtained=450.0, total_max=500.0, result_status="PASS")
        s3 = StudentResult(enrollment="S3", student_name="Third Person", status="Success", overall_percentage=85.0, total_obtained=425.0, total_max=500.0, result_status="PASS")
        s4 = StudentResult(enrollment="S4", student_name="Fourth Person", status="Success", overall_percentage=50.0, total_obtained=250.0, total_max=500.0, result_status="FAIL")

        students = [s3, s1, s4, s2]
        rankings = AcademicAnalytics.calculate_rankings(students)

        # Ranks must follow standard competition ranking: 1, 1, 3, 4
        ranks = [r["rank"] for r in rankings]
        self.assertEqual(ranks, [1, 1, 3, 4])
        self.assertEqual(rankings[0]["enrollment"], "S1")
        self.assertEqual(rankings[1]["enrollment"], "S2")
        self.assertEqual(rankings[2]["enrollment"], "S3")
        self.assertEqual(rankings[3]["enrollment"], "S4")

        # Class stats
        stats = AcademicAnalytics.calculate_class_statistics(students)
        self.assertEqual(stats["total_records"], 4)
        self.assertEqual(stats["passed_count"], 3)
        self.assertEqual(stats["reappear_count"], 1)
        self.assertEqual(stats["highest_percentage"], 90.0)
        self.assertEqual(stats["lowest_percentage"], 50.0)
        self.assertAlmostEqual(stats["average_percentage"], 78.75, places=2)
        self.assertAlmostEqual(stats["median_percentage"], 87.5, places=2)

    def test_11_formula_injection_defense(self):
        """Test formula injection sanitization on spreadsheet cell values."""
        # Malicious formula strings
        dangerous = ["=cmd|' /C calc'!A0", "+SUM(A1:A10)", "-2+3*cmd", "@SUM(B1)", "\tTAB_PAYLOAD", "\rCARRIAGE_PAYLOAD"]
        for payload in dangerous:
            sanitized = ResultExporter._sanitize_cell_value(payload)
            self.assertTrue(sanitized.startswith("'"), f"Failed for {payload}: got {sanitized}")

        # Safe values should remain untouched
        safe_values = ["Normal Student Name", 100, 85.5, True, None, "E2100456"]
        for safe in safe_values:
            self.assertEqual(ResultExporter._sanitize_cell_value(safe), safe)

    def test_12_job_cancellation(self):
        """Test job cancellation endpoint and processor status."""
        processor = get_batch_processor()
        job = processor.create_job(
            portal_url="https://results.university.edu/semester/exam",
            connector_id="demo_university",
            students=[{"enrollment": f"CANC_{i}", "name": f"Student {i}"} for i in range(100)],
            options={"include_totals": True}
        )
        processor.start_job(job.job_id)
        job_id = job.job_id
        # Cancel via API endpoint
        resp = self.client.post(f"/api/process/cancel/{job_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        # Check job status is cancelled
        job = processor.get_job(job_id)
        self.assertIsNotNone(job)
        self.assertIn(job.status, ("cancelled", "completed"))

    def test_13_individual_pdf_generation(self):
        """Test individual student PDF report generation."""
        student = StudentResult(
            enrollment="PDF001",
            roll_number="R9988",
            student_name="PDF Test Student",
            father_name="Father Name",
            institute="SkillSum Institute of Technology",
            branch="Information Technology",
            total_obtained=420.0,
            total_max=500.0,
            overall_percentage=84.0,
            result_status="PASS",
            division="First Division with Distinction",
            status="Success",
            subjects=[
                SubjectMarks(code="IT101", name="Software Engineering", theory_max=100, theory_obtained=85, total_max=100, total_obtained=85, percentage=85.0, status="PASS"),
                SubjectMarks(code="IT102", name="Database Systems", theory_max=100, theory_obtained=83, practical_max=50, practical_obtained=45, total_max=150, total_obtained=128, percentage=85.33, status="PASS")
            ]
        )
        pdf_path = os.path.join(self.test_dir, "test_student_provisional.pdf")
        gen_path = ResultExporter.generate_individual_student_pdf(student, pdf_path)
        self.assertTrue(os.path.exists(gen_path))
        self.assertGreater(os.path.getsize(gen_path), 1000)



if __name__ == "__main__":
    unittest.main()
