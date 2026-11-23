"""
Result Exporter for Excel generation, Subject-wise workbooks,
Individual PDF Performance Reports, and ZIP archives.
Includes Spreadsheet Formula Injection Protection and Academic Analytics Sheets.
"""
import json
import os
import zipfile
from typing import List, Dict, Any, Optional

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from connectors.base import StudentResult
from engine.analytics import AcademicAnalytics


class ResultExporter:
    """Exports processing results to Excel, PDF, and ZIP formats."""

    # Professional Brown + Cream palette
    HEADER_FILL = PatternFill(start_color="3E2723", end_color="3E2723", fill_type="solid")
    SUB_HEADER_FILL = PatternFill(start_color="654321", end_color="654321", fill_type="solid")
    ACCENT_FILL = PatternFill(start_color="F8F1E5", end_color="F8F1E5", fill_type="solid")
    PASS_FILL = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    FAIL_FILL = PatternFill(start_color="FFEBEE", end_color="FFEBEE", fill_type="solid")
    WARN_FILL = PatternFill(start_color="FFF8E1", end_color="FFF8E1", fill_type="solid")

    FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    FONT_BOLD = Font(name="Calibri", size=11, bold=True, color="30251F")
    FONT_REGULAR = Font(name="Calibri", size=11, color="30251F")
    FONT_PASS = Font(name="Calibri", size=11, bold=True, color="2E7D32")
    FONT_FAIL = Font(name="Calibri", size=11, bold=True, color="C62828")

    THIN_BORDER = Border(
        left=Side(style='thin', color="E8DCCB"),
        right=Side(style='thin', color="E8DCCB"),
        top=Side(style='thin', color="E8DCCB"),
        bottom=Side(style='thin', color="E8DCCB")
    )

    @classmethod
    def _sanitize_cell_value(cls, val: Any) -> Any:
        """
        Protect against CSV / Spreadsheet Formula Injection (CWE-1236).
        Prepends a single quote if text starts with formula triggers: =, +, -, @, \\t, \\r
        """
        if isinstance(val, str) and val:
            if val[0] in ('=', '+', '-', '@', '\t', '\r'):
                return "'" + val
        return val

    @classmethod
    def _auto_fit_columns(cls, ws):
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if "\n" in val_str:
                    lines = val_str.split("\n")
                    max_len = max(max_len, max(len(l) for l in lines))
                else:
                    max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    @classmethod
    def generate_consolidated_excel(
        cls,
        results: List[StudentResult],
        options: Dict[str, Any],
        filepath: str
    ) -> str:
        """
        Generate consolidated Excel workbook with:
        Sheet 1: Consolidated Results
        Sheet 2: Topper Rankings
        Sheet 3: Class Performance Summary
        Sheet 4: Verification & Integrity Flags
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Consolidated Results"

        include_all_subjects = options.get("include_all_subjects", True)
        include_totals = options.get("include_totals", True)
        include_percentage = options.get("include_percentage", True)
        include_status = options.get("include_status", True)

        # Discover unique subjects across results
        subjects_dict = {}
        for r in results:
            for s in r.subjects:
                key = s.code or s.name
                if key and key not in subjects_dict:
                    subjects_dict[key] = s.name or s.code

        # Build column headers
        headers = ["S.No", "Enrollment No", "Roll No", "Student Name", "Father Name", "Branch"]

        subject_cols_map = {}
        if include_all_subjects and subjects_dict:
            for sub_key, sub_name in subjects_dict.items():
                label = f"{sub_name} ({sub_key})" if sub_key != sub_name else sub_name
                headers.append(label)
                subject_cols_map[sub_key] = len(headers)

        if include_totals:
            headers.extend(["Total Obtained", "Maximum Marks"])
        if include_percentage:
            headers.append("Percentage (%)")
        if include_status:
            headers.extend(["Result Status", "Division"])
        headers.extend(["Process Status", "Verification Warnings", "Remarks / Errors"])

        # Write header row
        ws.append([cls._sanitize_cell_value(h) for h in headers])
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = cls.HEADER_FILL
            cell.font = cls.FONT_HEADER
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = cls.THIN_BORDER
        ws.row_dimensions[1].height = 28

        # Write data rows
        row_num = 2
        for idx, r in enumerate(results, 1):
            row_data = [
                idx,
                r.enrollment,
                r.roll_number or r.enrollment,
                r.student_name,
                r.father_name,
                r.branch
            ]

            if include_all_subjects and subjects_dict:
                student_sub_map = {s.code or s.name: s for s in r.subjects}
                for sub_key in subjects_dict:
                    sub = student_sub_map.get(sub_key)
                    if sub and sub.total_obtained is not None:
                        row_data.append(sub.total_obtained)
                    else:
                        row_data.append("-")

            if include_totals:
                row_data.append(r.total_obtained if r.total_obtained is not None else "-")
                row_data.append(r.total_max if r.total_max is not None else "-")

            if include_percentage:
                row_data.append(r.overall_percentage if r.overall_percentage is not None else "-")

            if include_status:
                row_data.append(r.result_status or "-")
                row_data.append(r.division or "-")

            row_data.append(r.status)
            row_data.append("; ".join(r.verification_flags) if r.verification_flags else "None")
            row_data.append(r.error_message or "")

            sanitized_row = [cls._sanitize_cell_value(v) for v in row_data]
            ws.append(sanitized_row)

            # Style row
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=row_num, column=col_idx)
                cell.font = cls.FONT_REGULAR
                cell.border = cls.THIN_BORDER
                cell.alignment = Alignment(vertical="center", horizontal="center" if col_idx in (1, 2, 3) else "left")

                if include_status and headers[col_idx - 1] == "Result Status":
                    val = str(cell.value or "").upper()
                    if "PASS" in val:
                        cell.fill = cls.PASS_FILL
                        cell.font = cls.FONT_PASS
                    elif any(f in val for f in ["FAIL", "REAPPEAR", "BACK"]):
                        cell.fill = cls.FAIL_FILL
                        cell.font = cls.FONT_FAIL

            ws.row_dimensions[row_num].height = 20
            row_num += 1

        cls._auto_fit_columns(ws)

        # -------------------------------------------------------------
        # Sheet 2: Topper Rankings
        # -------------------------------------------------------------
        cls._add_topper_rankings_sheet(wb, results)

        # -------------------------------------------------------------
        # Sheet 3: Class Performance Summary & Subject Statistics
        # -------------------------------------------------------------
        cls._add_class_statistics_sheet(wb, results)

        # -------------------------------------------------------------
        # Sheet 4: Verification & Integrity Flags
        # -------------------------------------------------------------
        cls._add_verification_sheet(wb, results)

        wb.save(filepath)
        return filepath

    @classmethod
    def _add_topper_rankings_sheet(cls, wb: openpyxl.Workbook, results: List[StudentResult]):
        """Add dedicated Topper Rankings sheet with competition rank logic (1224)."""
        ws = wb.create_sheet(title="Topper Rankings")
        rankings = AcademicAnalytics.calculate_rankings(results)

        headers = ["Rank", "Enrollment No", "Roll No", "Student Name", "Branch", "Total Obtained", "Maximum Marks", "Percentage (%)", "Result", "Division"]
        ws.append([cls._sanitize_cell_value(h) for h in headers])

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = cls.SUB_HEADER_FILL
            cell.font = cls.FONT_HEADER
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = cls.THIN_BORDER
        ws.row_dimensions[1].height = 26

        row_num = 2
        for rk in rankings:
            row_data = [
                f"Rank #{rk['rank']}",
                rk["enrollment"],
                rk["roll_number"],
                rk["student_name"],
                rk["branch"],
                rk["total_obtained"],
                rk["total_max"],
                f"{rk['overall_percentage']}%",
                rk["result_status"],
                rk["division"]
            ]
            sanitized = [cls._sanitize_cell_value(v) for v in row_data]
            ws.append(sanitized)

            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=row_num, column=col_idx)
                cell.font = cls.FONT_REGULAR
                cell.border = cls.THIN_BORDER
                cell.alignment = Alignment(vertical="center", horizontal="center" if col_idx in (1, 2, 3, 8) else "left")

                if col_idx == 1:
                    cell.font = cls.FONT_BOLD
                    if rk['rank'] == 1:
                        cell.fill = cls.PASS_FILL

            ws.row_dimensions[row_num].height = 20
            row_num += 1

        cls._auto_fit_columns(ws)

    @classmethod
    def _add_class_statistics_sheet(cls, wb: openpyxl.Workbook, results: List[StudentResult]):
        """Add overall academic metrics and subject-wise performance."""
        ws = wb.create_sheet(title="Performance Summary")
        stats = AcademicAnalytics.calculate_class_statistics(results)

        # Overview Metrics Table
        ws.append(["Metric", "Value", "Notes"])
        metric_rows = [
            ["Total Student Records", stats["total_records"], "All records submitted in input batch"],
            ["Successfully Processed", stats["processed_count"], "Records with successfully retrieved results"],
            ["Passed Students", stats["passed_count"], "Students with clear Pass status"],
            ["Reappear / Backlog Students", stats["reappear_count"], "Students with backlogs or fail evaluations"],
            ["Pass Percentage", f"{stats['pass_percentage']}%", stats["denominator_explanation"]],
            ["Highest Overall Percentage", f"{stats['highest_percentage']}%" if stats['highest_percentage'] else "N/A", "Top scoring student"],
            ["Lowest Overall Percentage", f"{stats['lowest_percentage']}%" if stats['lowest_percentage'] else "N/A", "Lowest scoring completed student"],
            ["Class Average Percentage", f"{stats['average_percentage']}%" if stats['average_percentage'] else "N/A", "Arithmetic mean of valid percentages"],
            ["Median Percentage", f"{stats['median_percentage']}%" if stats['median_percentage'] else "N/A", "Median of valid student percentages"],
            ["Failed / Timed-out Queries", stats["failed_count"], "Queries that could not be completed on portal"],
        ]

        for col_idx in range(1, 4):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = cls.HEADER_FILL
            cell.font = cls.FONT_HEADER
            cell.border = cls.THIN_BORDER
        ws.row_dimensions[1].height = 26

        for r_idx, r_data in enumerate(metric_rows, 2):
            ws.append([cls._sanitize_cell_value(v) for v in r_data])
            for c_idx in range(1, 4):
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.font = cls.FONT_BOLD if c_idx == 1 else cls.FONT_REGULAR
                cell.border = cls.THIN_BORDER
            ws.row_dimensions[r_idx].height = 20

        # Blank space
        ws.append([])
        ws.append([])

        # Subject-wise Breakdown Table
        subj_header_row = ws.max_row + 1
        subj_headers = ["Sub Code", "Subject Name", "Max Marks", "Highest", "Lowest", "Average", "Median", "Pass Count", "Fail Count", "Total Appeared"]
        ws.append([cls._sanitize_cell_value(h) for h in subj_headers])

        for c_idx in range(1, len(subj_headers) + 1):
            cell = ws.cell(row=subj_header_row, column=c_idx)
            cell.fill = cls.SUB_HEADER_FILL
            cell.font = cls.FONT_HEADER
            cell.border = cls.THIN_BORDER
        ws.row_dimensions[subj_header_row].height = 26

        for sitem in stats.get("subject_statistics", []):
            row_data = [
                sitem["code"],
                sitem["name"],
                sitem["total_max"] or "-",
                sitem["highest_marks"] if sitem["highest_marks"] is not None else "-",
                sitem["lowest_marks"] if sitem["lowest_marks"] is not None else "-",
                sitem["average_marks"] if sitem["average_marks"] is not None else "-",
                sitem["median_marks"] if sitem["median_marks"] is not None else "-",
                sitem["passed_count"],
                sitem["failed_count"],
                sitem["total_appeared"]
            ]
            ws.append([cls._sanitize_cell_value(v) for v in row_data])
            cur_r = ws.max_row
            for c_idx in range(1, len(subj_headers) + 1):
                cell = ws.cell(row=cur_r, column=c_idx)
                cell.font = cls.FONT_REGULAR
                cell.border = cls.THIN_BORDER
            ws.row_dimensions[cur_r].height = 20

        cls._auto_fit_columns(ws)

    @classmethod
    def _add_verification_sheet(cls, wb: openpyxl.Workbook, results: List[StudentResult]):
        """Add Verification Flags sheet documenting any data discrepancies or alerts."""
        ws = wb.create_sheet(title="Verification Flags")
        headers = ["S.No", "Enrollment No", "Student Name", "Verification Status", "Flag Count", "Verification Alert Details"]
        ws.append([cls._sanitize_cell_value(h) for h in headers])

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = cls.SUB_HEADER_FILL
            cell.font = cls.FONT_HEADER
            cell.border = cls.THIN_BORDER
        ws.row_dimensions[1].height = 26

        flagged_count = 0
        for idx, r in enumerate(results, 1):
            has_flags = bool(r.verification_flags)
            if has_flags:
                flagged_count += 1
            row_data = [
                idx,
                r.enrollment,
                r.student_name,
                "Requires Review" if has_flags else "Verified Clean",
                len(r.verification_flags),
                "; ".join(r.verification_flags) if has_flags else "All boundary checks passed."
            ]
            ws.append([cls._sanitize_cell_value(v) for v in row_data])
            cur_r = ws.max_row
            for c_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=cur_r, column=c_idx)
                cell.font = cls.FONT_REGULAR
                cell.border = cls.THIN_BORDER
                if c_idx == 4 and has_flags:
                    cell.fill = cls.WARN_FILL
                    cell.font = cls.FONT_BOLD
            ws.row_dimensions[cur_r].height = 20

        cls._auto_fit_columns(ws)

    @classmethod
    def generate_subject_wise_excel(
        cls,
        results: List[StudentResult],
        options: Dict[str, Any],
        filepath: str
    ) -> str:
        """
        Generate Excel workbook with a separate tab for each subject,
        displaying Theory, Practical, Internal, and Total marks.
        """
        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        subjects_dict = {}
        for r in results:
            for s in r.subjects:
                key = s.code or s.name
                if key and key not in subjects_dict:
                    subjects_dict[key] = s

        if not subjects_dict:
            ws = wb.create_sheet(title="Subjects")
            ws.append(["Notice", "No individual subject tables were extracted for these records."])
            wb.save(filepath)
            return filepath

        for sub_key, sample_sub in subjects_dict.items():
            sheet_title = (sample_sub.name or sub_key)[:28].replace("/", "-").replace(":", "-")
            ws = wb.create_sheet(title=sheet_title)

            headers = [
                "S.No", "Enrollment No", "Student Name",
                "Theory Max", "Theory Obtained",
                "Practical Max", "Practical Obtained",
                "Internal Obtained",
                "Total Marks", "Subject %", "Evaluation"
            ]
            ws.append([cls._sanitize_cell_value(h) for h in headers])

            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.fill = cls.SUB_HEADER_FILL
                cell.font = cls.FONT_HEADER
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = cls.THIN_BORDER
            ws.row_dimensions[1].height = 26

            row_num = 2
            for idx, r in enumerate(results, 1):
                sub = next((s for s in r.subjects if (s.code or s.name) == sub_key), None)
                if not sub:
                    continue

                row_data = [
                    idx,
                    r.enrollment,
                    r.student_name,
                    sub.theory_max if sub.theory_max is not None else "-",
                    sub.theory_obtained if sub.theory_obtained is not None else "-",
                    sub.practical_max if sub.practical_max is not None else "-",
                    sub.practical_obtained if sub.practical_obtained is not None else "-",
                    sub.internal_obtained if sub.internal_obtained is not None else "-",
                    sub.total_obtained if sub.total_obtained is not None else "-",
                    f"{sub.percentage}%" if sub.percentage is not None else "-",
                    sub.status or "-"
                ]
                ws.append([cls._sanitize_cell_value(v) for v in row_data])

                for col_idx in range(1, len(headers) + 1):
                    cell = ws.cell(row=row_num, column=col_idx)
                    cell.font = cls.FONT_REGULAR
                    cell.border = cls.THIN_BORDER
                    cell.alignment = Alignment(vertical="center", horizontal="center" if col_idx != 3 else "left")

                    if headers[col_idx - 1] == "Evaluation":
                        val = str(cell.value or "").upper()
                        if "PASS" in val:
                            cell.fill = cls.PASS_FILL
                            cell.font = cls.FONT_PASS
                        elif "FAIL" in val:
                            cell.fill = cls.FAIL_FILL
                            cell.font = cls.FONT_FAIL

                ws.row_dimensions[row_num].height = 20
                row_num += 1

            cls._auto_fit_columns(ws)

        wb.save(filepath)
        return filepath

    @classmethod
    def generate_individual_student_pdf(
        cls,
        result: StudentResult,
        filepath: str
    ) -> str:
        """
        Generate a clean, standardized Provisional Academic Performance Report PDF for a student
        using ReportLab. Clearly labeled as a processed report, not an official marksheet.
        """
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

            # Document Title
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=17,
                leading=21,
                alignment=1,
                textColor=colors.HexColor("#3E2723")
            )
            sub_style = ParagraphStyle(
                'DocSub',
                parent=styles['Normal'],
                fontSize=9,
                leading=12,
                alignment=1,
                textColor=colors.HexColor("#75685E")
            )
            disclaimer_style = ParagraphStyle(
                'DocDisclaimer',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                alignment=1,
                textColor=colors.HexColor("#B91C1C")
            )

            elements.append(Paragraph("<b>SKILLSUM RESULTSETU &bull; ACADEMIC REPORT</b>", title_style))
            elements.append(Paragraph("PROVISIONAL PERFORMANCE SUMMARY (NOT AN OFFICIAL UNIVERSITY MARKSHEET)", disclaimer_style))
            elements.append(Paragraph("<font size=7 color='#75685E'>Developed by SkillSum Innovations &bull; Founded by Aditya Rajak</font>", sub_style))
            elements.append(Spacer(1, 10))

            # Student Metadata Table
            meta_data = [
                [f"<b>Enrollment No:</b> {result.enrollment}", f"<b>Roll No:</b> {result.roll_number or result.enrollment}"],
                [f"<b>Student Name:</b> {result.student_name or 'N/A'}", f"<b>Father's Name:</b> {result.father_name or 'N/A'}"],
                [f"<b>Branch:</b> {result.branch or 'General'}", f"<b>Semester:</b> {result.semester or 'N/A'}"],
                [f"<b>Institute:</b> {result.institute or 'N/A'}", f"<b>Session:</b> {result.exam_session or 'N/A'}"],
            ]
            meta_table = Table(
                [[Paragraph(cell, styles['Normal']) for cell in row] for row in meta_data],
                colWidths=[270, 270]
            )
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F5F4")),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E7E5E4")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E7E5E4")),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(meta_table)
            elements.append(Spacer(1, 12))

            # Subjects Table
            if result.subjects:
                headers = ["Code", "Subject Name", "Th Max", "Th Obt", "Pr Max", "Pr Obt", "Int Obt", "Total", "Status"]
                rows = [headers]
                for s in result.subjects:
                    rows.append([
                        s.code or "-",
                        s.name or "-",
                        str(int(s.theory_max)) if s.theory_max is not None else "-",
                        str(s.theory_obtained) if s.theory_obtained is not None else "-",
                        str(int(s.practical_max)) if s.practical_max is not None else "-",
                        str(s.practical_obtained) if s.practical_obtained is not None else "-",
                        str(s.internal_obtained) if s.internal_obtained is not None else "-",
                        f"{s.total_obtained} / {s.total_max}" if s.total_max else (str(s.total_obtained) if s.total_obtained else "-"),
                        s.status or "-"
                    ])
                stbl = Table(rows, colWidths=[50, 180, 45, 45, 45, 45, 45, 55, 45])
                stbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#654321")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E8DCCB")),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF9F0")]),
                ]))
                elements.append(stbl)
                elements.append(Spacer(1, 12))

            # Summary Results Table
            summary_data = [
                ["Grand Total", f"{result.total_obtained} / {result.total_max}" if result.total_max else (str(result.total_obtained) or "N/A")],
                ["Overall Percentage", f"{result.overall_percentage}%" if result.overall_percentage is not None else "N/A"],
                ["Evaluation Status", result.result_status or "N/A"],
                ["Division", result.division or "N/A"],
            ]
            if result.verification_flags:
                summary_data.append(["Integrity Notices", "; ".join(result.verification_flags)])

            sum_table = Table(summary_data, colWidths=[180, 360])
            sum_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F1E5")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E8DCCB")),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(sum_table)

            doc.build(elements)
            return filepath
        except Exception as e:
            return ""

    @classmethod
    def create_marksheets_zip(cls, pdf_files: List[str], zip_filepath: str) -> str:
        """Create a ZIP archive containing all student marksheet PDFs."""
        with zipfile.ZipFile(zip_filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for fpath in pdf_files:
                if fpath and os.path.exists(fpath):
                    arcname = os.path.basename(fpath)
                    zf.write(fpath, arcname=arcname)
        return zip_filepath

    @classmethod
    def create_complete_package_zip(
        cls,
        consolidated_excel: str,
        subject_excel: Optional[str],
        pdf_files: List[str],
        summary_data: Dict[str, Any],
        zip_filepath: str
    ) -> str:
        """Create complete package ZIP with Excel sheets, PDFs, and report JSON."""
        with zipfile.ZipFile(zip_filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            if consolidated_excel and os.path.exists(consolidated_excel):
                zf.write(consolidated_excel, arcname="consolidated_results.xlsx")

            if subject_excel and os.path.exists(subject_excel):
                zf.write(subject_excel, arcname="subject_wise_results.xlsx")

            for fpath in pdf_files:
                if fpath and os.path.exists(fpath):
                    arcname = os.path.join("marksheets", os.path.basename(fpath))
                    zf.write(fpath, arcname=arcname)

            summary_bytes = json.dumps(summary_data, indent=2).encode('utf-8')
            zf.writestr("summary_report.json", summary_bytes)

        return zip_filepath
