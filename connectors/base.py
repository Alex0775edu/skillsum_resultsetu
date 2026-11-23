"""
Base classes and data models for result portal connectors.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class SubjectMarks:
    """Represents marks and evaluation for an individual subject."""
    code: str = ""
    name: str = ""
    theory_max: Optional[float] = None
    theory_min: Optional[float] = None
    theory_obtained: Optional[float] = None
    practical_max: Optional[float] = None
    practical_min: Optional[float] = None
    practical_obtained: Optional[float] = None
    internal_max: Optional[float] = None
    internal_min: Optional[float] = None
    internal_obtained: Optional[float] = None
    total_max: Optional[float] = None
    total_obtained: Optional[float] = None
    percentage: Optional[float] = None
    grade: str = ""
    status: str = ""  # e.g., "PASS", "FAIL", "DET", "ABS"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StudentResult:
    """Represents the complete result record for a single student."""
    enrollment: str = ""
    roll_number: str = ""
    student_name: str = ""
    father_name: str = ""
    branch: str = ""
    institute: str = ""
    semester: str = ""
    exam_session: str = ""
    subjects: List[SubjectMarks] = field(default_factory=list)
    total_max: Optional[float] = None
    total_obtained: Optional[float] = None
    overall_percentage: Optional[float] = None
    result_status: str = ""  # "PASS", "FAIL", "REAPPEAR", etc.
    division: str = ""
    status: str = "Pending"  # "Success", "Failed", "Skipped", "Cached"
    error_message: str = ""
    pdf_path: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["subjects"] = [s.to_dict() if isinstance(s, SubjectMarks) else s for s in self.subjects]
        return data


class BaseConnector(ABC):
    """
    Abstract base class for all university and college result portal connectors.
    Every connector must specify required input fields, URL matching pattern,
    and the logic to fetch/extract result data.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique machine identifier for the connector, e.g. 'bteup'."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of the portal/university, e.g. 'Board of Technical Education UP'."""
        pass

    @property
    @abstractmethod
    def default_url(self) -> str:
        """Default or typical result portal URL."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of portal format and authentication/parameters."""
        pass

    @property
    @abstractmethod
    def required_fields(self) -> List[Dict[str, Any]]:
        """
        List of required student metadata fields needed to query this portal.
        Example:
        [
            {"key": "enrollment", "label": "Enrollment Number", "type": "text", "required": True},
            {"key": "dob", "label": "Date of Birth (DD/MM/YYYY)", "type": "date", "required": True}
        ]
        """
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Determine if this connector can handle the provided result URL."""
        pass

    def initialize(self) -> None:
        """Lifecycle hook to initialize resources (e.g. browser driver, session)."""
        pass

    def cleanup(self) -> None:
        """Lifecycle hook to release resources (e.g. close driver, terminate session)."""
        pass

    @abstractmethod
    def fetch_result(
        self,
        portal_url: str,
        student_data: Dict[str, Any],
        options: Dict[str, Any],
        output_dir: str,
    ) -> StudentResult:
        """
        Query the portal for one student's result, parse values, optionally save PDF,
        and return a populated StudentResult object.
        """
        pass
