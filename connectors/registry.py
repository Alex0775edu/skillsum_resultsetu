"""
Connector registry for managing and matching portal connectors.
"""
from typing import Dict, List, Optional, Type
from urllib.parse import urlparse

from .base import BaseConnector
from .bteup_connector import BTEUPConnector
from .demo_connector import DemoUniversityConnector


class ConnectorRegistry:
    """Registry that manages available university result connectors."""

    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        # Register standard connectors
        self.register(BTEUPConnector(headless=True))
        self.register(DemoUniversityConnector())

    def register(self, connector: BaseConnector) -> None:
        self._connectors[connector.id] = connector

    def get_by_id(self, connector_id: str) -> Optional[BaseConnector]:
        return self._connectors.get(connector_id)

    def find_connector_for_url(self, url: str) -> Optional[BaseConnector]:
        """Match a URL to an available connector."""
        if not url:
            return None
        cleaned_url = url.strip()
        for connector in self._connectors.values():
            if connector.can_handle(cleaned_url):
                return connector
        return None

    def list_portals(self) -> List[Dict]:
        """Return information about all supported portals."""
        portals = []
        for c in self._connectors.values():
            portals.append({
                "id": c.id,
                "name": c.name,
                "default_url": c.default_url,
                "description": c.description,
                "required_fields": c.required_fields,
            })
        return portals

    def validate_url(self, url: str) -> Dict:
        """
        Validate URL and return matching connector metadata or an explanation
        if the portal is unsupported.
        """
        if not url or not url.strip():
            return {
                "valid": False,
                "supported": False,
                "message": "URL cannot be empty."
            }

        url = url.strip()
        parsed = urlparse(url)
        # Check scheme
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)

        if not parsed.netloc and not url.startswith("demo://"):
            return {
                "valid": False,
                "supported": False,
                "message": f"Invalid URL format: '{url}'"
            }

        connector = self.find_connector_for_url(url)
        if connector:
            return {
                "valid": True,
                "supported": True,
                "connector_id": connector.id,
                "portal_name": connector.name,
                "description": connector.description,
                "required_fields": connector.required_fields,
                "message": f"Successfully matched with {connector.name} connector."
            }

        # Not supported
        supported_names = [f"• {c.name} ({c.default_url})" for c in self._connectors.values()]
        return {
            "valid": True,
            "supported": False,
            "message": (
                f"No compatible connector found for portal '{parsed.netloc}'. "
                f"Each university portal has unique HTML form structures, validation, and layout. "
                f"To process results from this portal, a custom connector can be added under connectors/. "
                f"\n\nCurrently supported portals:\n" + "\n".join(supported_names)
            ),
            "supported_portals": self.list_portals()
        }


# Global singleton instance
_registry_instance: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ConnectorRegistry()
    return _registry_instance
