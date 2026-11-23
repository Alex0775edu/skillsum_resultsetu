"""
Result Exporter for Excel generation, Subject-wise workbooks, and ZIP archives.
Ensures dynamic calculations and preserves original marksheet data.
"""
import json
import os
import zipfile
from typing import List, Dict, Any, Optional

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from connectors.base import StudentResult


class ResultExporter:
    """Exports processing results to Excel and ZIP formats."""

    # Color palette
    HEADER_FILL = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    SUB_HEADER_FILL = PatternFill(start_color="2B6CB0", end_color="2B6CB0", fill_type="solid")
    ACCENT_FILL = PatternFill(start_color="EDF2F7", end_color="EDF2F7", fill_type="solid")
    PASS_FILL = PatternFill(start_color="C6F6D5", end_color="C6F6D5", fill_type="solid")
    FAIL_FILL = PatternFill(start_color="FED7D7", end_color="FED7D7", fill_type="solid")

    FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    FONT_BOLD = Font(name="Calibri", size=11, bold=True)
    FONT_REGULAR = Font(name="Calibri", size=11)
    FONT_PASS = Font(name="Calibri", size=11, bold=True, color="22543D")
    FONT_FAIL = Font(name="Calibri", size=11, bold=True, color="742A2A")

    THIN_BORDER = Border(
        left=Side(style='thin', color="CBD5E0"),
        right=Side(style='thin', color="CBD5E0"),
        top=Side(style='thin', color="CBD5E0"),
        bottom=Side(style='thin', color="CBD5E0")
    )

    @classmethod
    def _auto_fit_columns(cls, ws):
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                # Skip merged or formula text length blowup
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
        Generate consolidated Excel workbook containing all student records,
        evaluation summary, and dynamic totals.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Consolidated Results"

        # Determine if subjects should be included in consolidated sheet
        include_all_subjects = options.get("include_all_subjects", True)
        include_theory = options.get("include_theory", True)
        include_practical = options.get("include_practical", True)
        include_internal = options.get("include_internal", True)
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
        headers.extend(["Process Status", "Remarks / Errors"])

        # Write header row
        ws.append(headers)
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
            row_data.append(r.error_message or "")

            ws.append(row_data)

            # Style row
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=row_num, column=col_idx)
                cell.font = cls.FONT_REGULAR
                cell.border = cls.THIN_BORDER
                cell.alignment = Alignment(vertical="center", horizontal="center" if col_idx in (1, 2, 3) else "left")

                # Highlight Pass/Fail
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
        wb.save(filepath)
        return filepath

    @classmethod
    def generate_subject_wise_excel(
        cls,
        results: List[StudentResult],
        options: Dict[str, Any],
        filepath: str
    ) -> str:
        """
        Generate an Excel workbook with a separate tab for each subject,
        displaying Theory, Practical, Internal, and Total marks.
        """
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # Discover unique subjects across results
        subjects_dict = {}
        for r in results:
            for s in r.subjects:
                key = s.code or s.name
                if key and key not in subjects_dict:
                    subjects_dict[key] = s

        if not subjects_dict:
            # Create a placeholder sheet if no subject tables were present
            ws = wb.create_sheet(title="Subjects")
            ws.append(["Notice", "No structured individual subject tables were extracted for these records."])
            wb.save(filepath)
            return filepath

        for sub_key, sample_sub in subjects_dict.items():
            sheet_title = (sample_sub.name or sub_key)[:28].replace("/", "-").replace(":", "-")
            ws = wb.create_sheet(title=sheet_title)

            # Headers
            headers = [
                "S.No", "Enrollment No", "Student Name",
                "Theory Max", "Theory Obtained",
                "Practical Max", "Practical Obtained",
                "Internal Obtained",
                "Total Marks", "Subject %", "Evaluation"
            ]
            ws.append(headers)

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
                ws.append(row_data)

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
    def create_marksheets_zip(
        cls,
        pdf_files: List[str],
        zip_filepath: str
    ) -> str:
        """Create a ZIP archive containing all downloaded student marksheet PDFs/PNGs."""
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
        """
        Create a complete result package ZIP archive containing:
        - consolidated_results.xlsx
        - subject_wise_results.xlsx
        - marksheets/ (folder of all PDFs)
        - summary_report.json
        """
        with zipfile.ZipFile(zip_filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            if consolidated_excel and os.path.exists(consolidated_excel):
                zf.write(consolidated_excel, arcname="consolidated_results.xlsx")

            if subject_excel and os.path.exists(subject_excel):
                zf.write(subject_excel, arcname="subject_wise_results.xlsx")

            # Add marksheets inside marksheets/ subfolder
            for fpath in pdf_files:
                if fpath and os.path.exists(fpath):
                    arcname = os.path.join("marksheets", os.path.basename(fpath))
                    zf.write(fpath, arcname=arcname)

            # Add summary json
            summary_bytes = json.dumps(summary_data, indent=2).encode('utf-8')
            zf.writestr("summary_report.json", summary_bytes)

        return zip_filepath
