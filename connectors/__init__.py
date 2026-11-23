"""
Result Downloader Portal Connectors Package
"""
from .base import BaseConnector, SubjectMarks, StudentResult
from .registry import ConnectorRegistry, get_registry

__all__ = ["BaseConnector", "SubjectMarks", "StudentResult", "ConnectorRegistry", "get_registry"]
