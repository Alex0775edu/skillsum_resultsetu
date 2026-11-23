"""
Academic Analytics, Topper Ranking, Statistics, and Result Verification Engine.
Handles competition ranking, subject statistics, backlog detection, and integrity checks.
"""
import statistics
from typing import List, Dict, Any, Optional, Tuple

from connectors.base import StudentResult, SubjectMarks


class ResultVerifier:
    """Verifies academic result consistency, marks boundaries, and data integrity."""

    @classmethod
    def verify(cls, result: StudentResult) -> List[str]:
        """
        Verify an individual student's extracted result.
        Returns a list of warning or verification flags. Never modifies marks.
        """
        flags = []

        if result.status != "Success" and result.status != "Cached":
            return flags

        # Check total marks boundaries
        if result.total_obtained is not None and result.total_max is not None:
            if result.total_obtained < 0:
                flags.append("Suspicious: Negative total marks obtained.")
            if result.total_max <= 0:
                flags.append("Suspicious: Maximum total marks is zero or negative.")
            elif result.total_obtained > result.total_max:
                flags.append(f"Integrity Alert: Obtained total ({result.total_obtained}) exceeds maximum ({result.total_max}).")

        # Check percentage calculation consistency
        if result.total_obtained is not None and result.total_max is not None and result.total_max > 0:
            expected_pct = round((result.total_obtained / result.total_max) * 100, 2)
            if result.overall_percentage is not None:
                if abs(result.overall_percentage - expected_pct) > 1.0:
                    flags.append(f"Discrepancy: Extracted percentage ({result.overall_percentage}%) differs from computed ({expected_pct}%).")

        # Check subject level evaluation
        for s in result.subjects:
            sub_id = s.code or s.name or "Unknown Subject"

            # Theory checks
            if s.theory_obtained is not None and s.theory_max is not None:
                if s.theory_obtained < 0:
                    flags.append(f"{sub_id}: Negative theory marks.")
                if s.theory_obtained > s.theory_max:
                    flags.append(f"{sub_id}: Theory obtained ({s.theory_obtained}) exceeds max ({s.theory_max}).")

            # Practical checks
            if s.practical_obtained is not None and s.practical_max is not None:
                if s.practical_obtained < 0:
                    flags.append(f"{sub_id}: Negative practical marks.")
                if s.practical_obtained > s.practical_max:
                    flags.append(f"{sub_id}: Practical obtained ({s.practical_obtained}) exceeds max ({s.practical_max}).")

            # Missing evaluation check
            if s.total_obtained is None and s.theory_obtained is None and s.practical_obtained is None:
                flags.append(f"{sub_id}: Marks unavailable or not published.")

        # Check incomplete extraction
        if (result.total_obtained is None) and (not result.subjects):
            flags.append("Incomplete: Neither summary total nor individual subjects were extracted.")

        return flags


class AcademicAnalytics:
    """Computes academic rankings, class statistics, and subject performance summaries."""

    @classmethod
    def calculate_rankings(cls, results: List[StudentResult]) -> List[Dict[str, Any]]:
        """
        Compute standard competition ranking (1224) for eligible students with valid percentages.
        Tied scores receive identical ranks; subsequent ranks skip accordingly.
        """
        # Filter students who have valid percentages and passed/completed
        eligible = []
        for r in results:
            if r.status in ("Success", "Cached") and r.overall_percentage is not None:
                eligible.append(r)

        # Sort descending by overall percentage, then total obtained
        sorted_students = sorted(
            eligible,
            key=lambda x: (x.overall_percentage or 0.0, x.total_obtained or 0.0),
            reverse=True
        )

        ranked_list = []
        current_rank = 1
        for idx, student in enumerate(sorted_students):
            if idx > 0:
                prev = sorted_students[idx - 1]
                # If tied with previous student in percentage and total
                if (student.overall_percentage == prev.overall_percentage and
                        student.total_obtained == prev.total_obtained):
                    # Keep same rank
                    rank_to_assign = ranked_list[-1]["rank"]
                else:
                    rank_to_assign = idx + 1
            else:
                rank_to_assign = 1

            ranked_list.append({
                "rank": rank_to_assign,
                "enrollment": student.enrollment,
                "roll_number": student.roll_number or student.enrollment,
                "student_name": student.student_name,
                "branch": student.branch,
                "total_obtained": student.total_obtained,
                "total_max": student.total_max,
                "overall_percentage": student.overall_percentage,
                "result_status": student.result_status,
                "division": student.division
            })

        return ranked_list

    @classmethod
    def calculate_class_statistics(cls, results: List[StudentResult]) -> Dict[str, Any]:
        """
        Compute comprehensive performance statistics, averages, pass rates,
        and subject-wise performance breakdown.
        """
        total_students = len(results)
        successful = [r for r in results if r.status in ("Success", "Cached")]
        failed_count = sum(1 for r in results if r.status == "Failed")
        skipped_count = sum(1 for r in results if r.status == "Skipped")

        # Academic evaluation counts
        passed_academic = 0
        reappear_academic = 0
        backlog_students = 0

        valid_percentages = []
        valid_totals = []

        for r in successful:
            if r.overall_percentage is not None:
                valid_percentages.append(r.overall_percentage)
            if r.total_obtained is not None:
                valid_totals.append(r.total_obtained)

            status_str = (r.result_status or "").upper()
            if "PASS" in status_str:
                passed_academic += 1
            elif any(f in status_str for f in ["FAIL", "REAPPEAR", "BACK", "SUPPL"]):
                reappear_academic += 1

            # Count failed subjects across student
            failed_subs = sum(1 for s in r.subjects if s.status and "FAIL" in s.status.upper())
            if failed_subs > 0:
                backlog_students += 1

        pass_percentage = round((passed_academic / len(successful)) * 100, 2) if successful else 0.0

        # Percentages metrics
        highest_pct = max(valid_percentages) if valid_percentages else None
        lowest_pct = min(valid_percentages) if valid_percentages else None
        avg_pct = round(statistics.mean(valid_percentages), 2) if valid_percentages else None
        median_pct = round(statistics.median(valid_percentages), 2) if valid_percentages else None

        # Subject-wise statistics
        subject_stats = cls._compute_subject_statistics(successful)

        return {
            "total_records": total_students,
            "processed_count": len(successful),
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "passed_count": passed_academic,
            "reappear_count": reappear_academic,
            "backlog_students_count": backlog_students,
            "pass_percentage": pass_percentage,
            "highest_percentage": highest_pct,
            "lowest_percentage": lowest_pct,
            "average_percentage": avg_pct,
            "median_percentage": median_pct,
            "subject_statistics": subject_stats,
            "denominator_explanation": f"Pass percentage is calculated as ({passed_academic} passed / {len(successful)} processed students)."
        }

    @classmethod
    def _compute_subject_statistics(cls, results: List[StudentResult]) -> List[Dict[str, Any]]:
        """Compute highest, lowest, average, and pass count per subject."""
        subjects_data: Dict[str, Dict[str, Any]] = {}

        for r in results:
            for s in r.subjects:
                key = s.code or s.name
                if not key:
                    continue
                if key not in subjects_data:
                    subjects_data[key] = {
                        "code": s.code,
                        "name": s.name or s.code,
                        "total_max": s.total_max,
                        "obtained_scores": [],
                        "passed": 0,
                        "failed": 0
                    }

                if s.total_obtained is not None:
                    subjects_data[key]["obtained_scores"].append(s.total_obtained)

                st = (s.status or "").upper()
                if "PASS" in st:
                    subjects_data[key]["passed"] += 1
                elif "FAIL" in st:
                    subjects_data[key]["failed"] += 1

        summary_list = []
        for key, sdata in subjects_data.items():
            scores = sdata["obtained_scores"]
            highest = max(scores) if scores else None
            lowest = min(scores) if scores else None
            avg = round(statistics.mean(scores), 2) if scores else None
            median = round(statistics.median(scores), 2) if scores else None

            summary_list.append({
                "code": sdata["code"],
                "name": sdata["name"],
                "total_max": sdata["total_max"],
                "highest_marks": highest,
                "lowest_marks": lowest,
                "average_marks": avg,
                "median_marks": median,
                "passed_count": sdata["passed"],
                "failed_count": sdata["failed"],
                "total_appeared": len(scores)
            })

        return summary_list
