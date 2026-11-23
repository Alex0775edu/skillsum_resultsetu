"""
Excel Upload Parser with Smart Validation, Column Auto-Detection,
Duplicate Review, and Record Verification.
"""
import io
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd


class ExcelParser:
    """Handles Excel file upload parsing, column auto-detection, preview, and validation."""

    COLUMN_SYNONYMS = {
        "enrollment": [
            "enrollment_number", "enrollment", "enrolment", "enrollmentno",
            "enrollment no", "enrolment no", "roll", "rollno", "roll no",
            "roll number", "registration", "reg no", "regno", "studentid",
            "student id", "enr", "enrno", "enr no", "enrollment_num", "roll_num", "seat_no"
        ],
        "dob": [
            "date_of_birth", "dob", "date of birth", "birthdate", "birth date",
            "birth", "dateofbirth", "d_o_b"
        ],
        "name": [
            "name", "student name", "student_name", "candidate name",
            "candidate_name", "student", "full_name"
        ],
        "father_name": [
            "father_name", "father name", "father's name", "fathers name", "guardian_name"
        ],
        "branch": [
            "branch", "branch_name", "department", "course", "stream", "discipline"
        ]
    }

    @staticmethod
    def _normalize_name(name: Any) -> str:
        return re.sub(r"[^a-z0-9]", "", str(name).lower())

    @classmethod
    def auto_detect_columns(cls, columns: List[str]) -> Dict[str, Optional[str]]:
        """
        Auto-detect standard fields from given column names.
        Returns a dict mapping standard keys ('enrollment', 'dob', etc.) to actual column names.
        """
        detected: Dict[str, Optional[str]] = {key: None for key in cls.COLUMN_SYNONYMS}
        normalized_cols = {cls._normalize_name(c): c for c in columns}

        for std_key, syn_list in cls.COLUMN_SYNONYMS.items():
            for syn in syn_list:
                norm_syn = cls._normalize_name(syn)
                if norm_syn in normalized_cols:
                    detected[std_key] = normalized_cols[norm_syn]
                    break

        return detected

    @classmethod
    def parse_file(
        cls, file_bytes: bytes, filename: str
    ) -> Dict[str, Any]:
        """
        Parse uploaded Excel file into dataframe and generate summary, preview,
        validation issues, and auto-detected mappings.
        """
        try:
            if filename.lower().endswith(".xls"):
                df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
            else:
                df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        except Exception as e:
            try:
                df = pd.read_excel(io.BytesIO(file_bytes))
            except Exception as ex:
                raise ValueError(f"Failed to read Excel file: {str(ex)}")

        columns = [str(c).strip() for c in df.columns]
        df.columns = columns

        detected_mapping = cls.auto_detect_columns(columns)

        # Detect preview rows (first 10)
        preview_records = []
        for idx, row in df.head(10).iterrows():
            rec = {}
            for col in columns:
                val = row[col]
                if pd.isna(val):
                    rec[col] = ""
                elif isinstance(val, (datetime, pd.Timestamp)):
                    rec[col] = val.strftime("%d/%m/%Y")
                else:
                    rec[col] = str(val).strip()
            preview_records.append(rec)

        total_rows = len(df)
        enrollment_col = detected_mapping.get("enrollment")

        duplicate_count = 0
        empty_count = 0
        valid_count = 0
        validation_issues: List[Dict[str, Any]] = []

        if enrollment_col and enrollment_col in df.columns:
            seen_enr = {}
            for row_idx, val in enumerate(df[enrollment_col], start=2):  # Row 2 is first data row
                if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
                    empty_count += 1
                    validation_issues.append({
                        "row": row_idx,
                        "type": "empty_identifier",
                        "severity": "warning",
                        "message": f"Row {row_idx}: Missing or blank identifier in '{enrollment_col}'."
                    })
                else:
                    val_str = str(int(val) if isinstance(val, float) and val.is_integer() else val).strip()
                    if val_str in seen_enr:
                        duplicate_count += 1
                        first_row = seen_enr[val_str]
                        validation_issues.append({
                            "row": row_idx,
                            "type": "duplicate_entry",
                            "severity": "warning",
                            "message": f"Row {row_idx}: Duplicate identifier '{val_str}' (first observed at Row {first_row})."
                        })
                    else:
                        seen_enr[val_str] = row_idx
                        valid_count += 1
        else:
            valid_count = total_rows

        return {
            "filename": filename,
            "total_rows": total_rows,
            "columns": columns,
            "detected_mapping": detected_mapping,
            "preview_records": preview_records,
            "duplicate_count": duplicate_count,
            "empty_count": empty_count,
            "valid_count": valid_count,
            "validation_issues": validation_issues[:50],  # Keep first 50 row issues
        }

    @classmethod
    def extract_student_records(
        cls,
        file_bytes: bytes,
        filename: str,
        column_mapping: Dict[str, str],
        remove_duplicates: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extract clean student records using verified or user-mapped column names.
        Returns extracted student dicts and comprehensive validation statistics.
        """
        if filename.lower().endswith(".xls"):
            df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
        else:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")

        columns = [str(c).strip() for c in df.columns]
        df.columns = columns

        enrollment_col = column_mapping.get("enrollment")
        dob_col = column_mapping.get("dob")
        name_col = column_mapping.get("name")
        father_col = column_mapping.get("father_name")
        branch_col = column_mapping.get("branch")

        if not enrollment_col or enrollment_col not in df.columns:
            raise ValueError(f"Selected Enrollment/Roll column '{enrollment_col}' was not found in the file.")

        records = []
        seen_enrollments = {}
        row_issues = []
        stats = {
            "total": len(df),
            "valid": 0,
            "duplicates": 0,
            "empty": 0,
            "issues": []
        }

        for idx, row in df.iterrows():
            row_num = idx + 2
            raw_enr = row[enrollment_col]

            if pd.isna(raw_enr):
                stats["empty"] += 1
                row_issues.append({"row": row_num, "reason": "Empty enrollment field"})
                continue

            # Format enrollment (convert float like 210123.0 to integer string)
            if isinstance(raw_enr, float) and raw_enr.is_integer():
                enrollment = str(int(raw_enr)).strip()
            else:
                enrollment = str(raw_enr).strip()

            if not enrollment or enrollment.lower() == "nan":
                stats["empty"] += 1
                row_issues.append({"row": row_num, "reason": "Empty/NaN enrollment value"})
                continue

            # Check duplicate
            if enrollment in seen_enrollments:
                stats["duplicates"] += 1
                first_seen = seen_enrollments[enrollment]
                row_issues.append({"row": row_num, "reason": f"Duplicate of Row {first_seen} ({enrollment})"})
                if remove_duplicates:
                    continue
            else:
                seen_enrollments[enrollment] = row_num

            # Date of birth formatting
            dob_val = ""
            if dob_col and dob_col in df.columns:
                raw_dob = row[dob_col]
                if not pd.isna(raw_dob):
                    if isinstance(raw_dob, (datetime, pd.Timestamp)):
                        dob_val = raw_dob.strftime("%d/%m/%Y")
                    else:
                        try:
                            dt = pd.to_datetime(raw_dob, dayfirst=True, errors="coerce")
                            if dt is not None and not pd.isna(dt):
                                dob_val = dt.strftime("%d/%m/%Y")
                            else:
                                dob_val = str(raw_dob).strip()
                        except Exception:
                            dob_val = str(raw_dob).strip()

            name_val = ""
            if name_col and name_col in df.columns and not pd.isna(row[name_col]):
                name_val = str(row[name_col]).strip()

            father_val = ""
            if father_col and father_col in df.columns and not pd.isna(row[father_col]):
                father_val = str(row[father_col]).strip()

            branch_val = ""
            if branch_col and branch_col in df.columns and not pd.isna(row[branch_col]):
                branch_val = str(row[branch_col]).strip()

            records.append({
                "row_index": row_num,
                "enrollment": enrollment,
                "roll_number": enrollment,
                "dob": dob_val,
                "name": name_val,
                "father_name": father_val,
                "branch": branch_val
            })
            stats["valid"] += 1

        stats["issues"] = row_issues
        return records, stats
