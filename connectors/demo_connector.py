"""
Demo & Standard University Result Portal Connector.
Provides a reference implementation of a multi-subject university result portal
for automated testing, validation, and offline demonstrations.
Generates genuine academic marksheet PDFs using ReportLab/PyMuPDF.
"""
import os
import random
from datetime import datetime
from typing import Dict, Any, List

from .base import BaseConnector, StudentResult, SubjectMarks


class DemoUniversityConnector(BaseConnector):
    """
    Reference connector representing standard university semester examination systems
    (e.g., Computer Science, Engineering, Applied Sciences).
    """

    id = "demo_university"
    name = "Standard University Examination Portal (Demo & Reference)"
    default_url = "https://results.university.edu/semester/exam"
    description = (
        "Built-in reference connector with full multi-subject evaluation "
        "(Theory, Practical, Internal, Total). Ideal for testing bulk processing and exports."
    )

    required_fields = [
        {
            "key": "enrollment",
            "label": "Enrollment Number / Roll Number",
            "type": "text",
            "required": True,
            "synonyms": [
                "enrollment", "enrolment", "roll", "rollno", "roll_no",
                "enrollment_no", "reg_no", "student_id"
            ]
        },
        {
            "key": "name",
            "label": "Student Name (Optional)",
            "type": "text",
            "required": False,
            "synonyms": ["name", "student_name", "candidate_name"]
        },
        {
            "key": "dob",
            "label": "Date of Birth (Optional)",
            "type": "date",
            "required": False,
            "synonyms": ["dob", "date_of_birth", "birthdate"]
        }
    ]

    COURSE_SUBJECTS = [
        ("CS401", "Operating Systems", 100, 50, 25),
        ("CS402", "Database Management Systems", 100, 50, 25),
        ("CS403", "Data Structures & Algorithms", 100, 50, 25),
        ("CS404", "Computer Networks", 100, 50, 25),
        ("CS405", "Software Engineering", 100, 0, 25),
    ]

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        clean = url.lower().strip()
        return any(k in clean for k in [
            "demo", "sample", "results.university.edu", "standard", "test-portal", "localhost"
        ])

    @staticmethod
    def _generate_marksheet_pdf(filepath: str, result: StudentResult) -> None:
        """Create a marksheet PDF for the student using ReportLab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            styles = getSampleStyleSheet()
            elements = []

            # University Header
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=18,
                leading=22,
                alignment=1,
                textColor=colors.HexColor("#1A365D")
            )
            sub_style = ParagraphStyle(
                'SubStyle',
                parent=styles['Normal'],
                fontSize=11,
                leading=14,
                alignment=1,
                textColor=colors.HexColor("#4A5568")
            )

            elements.append(Paragraph("<b>NATIONAL BOARD OF TECHNICAL EDUCATION & SCIENCES</b>", title_style))
            elements.append(Paragraph("SEMESTER EXAMINATION MARKSHEET (PROVISIONAL)", sub_style))
            elements.append(Spacer(1, 15))

            # Student Info Table
            info_data = [
                [f"<b>Enrollment No:</b> {result.enrollment}", f"<b>Roll No:</b> {result.roll_number or result.enrollment}"],
                [f"<b>Student Name:</b> {result.student_name}", f"<b>Father's Name:</b> {result.father_name}"],
                [f"<b>Branch:</b> {result.branch}", f"<b>Semester:</b> {result.semester}"],
                [f"<b>Institute:</b> {result.institute}", f"<b>Exam Session:</b> {result.exam_session}"],
            ]
            info_table = Table(
                [[Paragraph(cell, styles['Normal']) for cell in row] for row in info_data],
                colWidths=[270, 270]
            )
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 15))

            # Subjects Table
            headers = ["Sub Code", "Subject Name", "Th Max", "Th Obt", "Pr Max", "Pr Obt", "Int Obt", "Total", "Status"]
            table_rows = [headers]
            for s in result.subjects:
                table_rows.append([
                    s.code,
                    s.name,
                    str(int(s.theory_max)) if s.theory_max else "-",
                    str(int(s.theory_obtained)) if s.theory_obtained is not None else "-",
                    str(int(s.practical_max)) if s.practical_max else "-",
                    str(int(s.practical_obtained)) if s.practical_obtained is not None else "-",
                    str(int(s.internal_obtained)) if s.internal_obtained is not None else "-",
                    f"{int(s.total_obtained)} / {int(s.total_max)}",
                    s.status
                ])

            subj_table = Table(table_rows, colWidths=[55, 175, 45, 45, 45, 45, 45, 55, 45])
            subj_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ]))
            elements.append(subj_table)
            elements.append(Spacer(1, 15))

            # Summary Table
            summary_data = [
                ["Grand Total", f"{result.total_obtained} / {result.total_max}"],
                ["Overall Percentage", f"{result.overall_percentage}%"],
                ["Final Evaluation", result.result_status],
                ["Division", result.division],
            ]
            sum_table = Table(summary_data, colWidths=[200, 340])
            sum_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(sum_table)

            doc.build(elements)
        except Exception as e:
            # Fallback simple text file or pass
            print(f"PDF creation notice: {e}")

    def fetch_result(
        self,
        portal_url: str,
        student_data: Dict[str, Any],
        options: Dict[str, Any],
        output_dir: str,
    ) -> StudentResult:
        enrollment = str(student_data.get("enrollment") or "").strip()
        name = str(student_data.get("name") or "").strip()

        result = StudentResult(
            enrollment=enrollment,
            roll_number=str(student_data.get("roll_number") or enrollment),
            student_name=name or f"Student {enrollment[-4:] if len(enrollment) >= 4 else enrollment}",
            father_name=str(student_data.get("father_name") or "Mr. Academic Guardian"),
            branch=str(student_data.get("branch") or "Computer Science & Engineering"),
            institute="Institute of Technology & Engineering",
            semester="Semester 4",
            exam_session="Even Semester 2026",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if not enrollment or enrollment.lower() == "nan":
            result.status = "Skipped"
            result.error_message = "Empty enrollment or roll number"
            return result

        # Deterministic score generation based on enrollment seed
        seed_val = sum(ord(c) for c in enrollment)
        rng = random.Random(seed_val)

        # 5% chance of failing or missing record for simulation testing if test flag is active
        if enrollment.endswith("9999"):
            result.status = "Failed"
            result.error_message = "Record not found in examination database (404 Not Found)"
            return result

        total_obtained = 0.0
        total_max = 0.0
        all_passed = True

        subjects_list = []
        for code, sub_name, th_max, pr_max, int_max in self.COURSE_SUBJECTS:
            th_min = th_max * 0.33
            pr_min = pr_max * 0.40 if pr_max > 0 else 0

            # Deterministic marks
            th_obt = round(rng.uniform(th_min + 5, th_max - 5), 1)
            pr_obt = round(rng.uniform(pr_min + 3, pr_max - 2), 1) if pr_max > 0 else 0.0
            int_obt = round(rng.uniform(15, int_max), 1)

            sub_tot_max = th_max + pr_max + int_max
            sub_tot_obt = round(th_obt + pr_obt + int_obt, 1)
            sub_pct = round((sub_tot_obt / sub_tot_max) * 100, 2)
            passed = th_obt >= th_min and (pr_max == 0 or pr_obt >= pr_min)

            if not passed:
                all_passed = False

            subj = SubjectMarks(
                code=code,
                name=sub_name,
                theory_max=th_max,
                theory_min=th_min,
                theory_obtained=th_obt,
                practical_max=pr_max if pr_max > 0 else None,
                practical_min=pr_min if pr_max > 0 else None,
                practical_obtained=pr_obt if pr_max > 0 else None,
                internal_max=int_max,
                internal_min=int_max * 0.4,
                internal_obtained=int_obt,
                total_max=sub_tot_max,
                total_obtained=sub_tot_obt,
                percentage=sub_pct,
                status="PASS" if passed else "FAIL"
            )
            subjects_list.append(subj)
            total_obtained += sub_tot_obt
            total_max += sub_tot_max

        result.subjects = subjects_list
        result.total_obtained = round(total_obtained, 1)
        result.total_max = round(total_max, 1)
        result.overall_percentage = round((total_obtained / total_max) * 100, 2) if total_max else 0
        result.result_status = "PASS" if all_passed else "REAPPEAR"
        result.division = (
            "First Division with Distinction" if result.overall_percentage >= 75
            else "First Division" if result.overall_percentage >= 60
            else "Second Division" if result.overall_percentage >= 50
            else "Pass Class" if all_passed else "Fail"
        )

        base_name = "".join(ch for ch in enrollment if ch.isalnum() or ch in ("_", "-"))
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

        if options.get("download_pdf", True):
            os.makedirs(output_dir, exist_ok=True)
            self._generate_marksheet_pdf(pdf_path, result)
            result.pdf_path = pdf_path

        result.status = "Success"
        return result
