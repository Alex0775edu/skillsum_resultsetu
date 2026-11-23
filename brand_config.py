"""
Project Identity & Branding Configuration Module.
All product names, owner details, taglines, and support contacts are centralized here.
Do NOT hardcode brand names across the application; reference this module instead.
"""
from typing import Dict, Any

# --- Configurable Project Identity ---
PROJECT_NAME = "SkillSum ResultSetu"
PROJECT_SHORT_NAME = "ResultSetu"
PROJECT_SLUG = "skillsum-resultsetu"
TAGLINE = "Simplify bulk academic result processing."
OWNER_NAME = "SkillSum Innovations"
FOUNDER_NAME = "Aditya Rajak"
COMPANY_URL = "https://skillsum.in/"
POSITIONING = "An independent, free and open-source academic result processing utility."
LICENSE_NAME = "MIT License"
SUPPORT_EMAIL = "[SUPPORT_EMAIL_PLACEHOLDER]"  # Clearly marked placeholder as instructed
REPO_URL = "https://github.com/Alex0775edu/skillsum_resultsetu"
VERSION = "2.1.0"

# --- Privacy & Architecture Constraints ---
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB maximum upload limit
JOB_RETENTION_MINUTES = 30  # Server-side temp file automatic TTL
ANALYTICS_ENABLED = False  # Strictly False: No analytics, tracking, or ads
LOCAL_STORAGE_PREFERENCE = True  # Prefer browser-side parsing before upload


def get_branding_context() -> Dict[str, Any]:
    """Return dictionary of all branding settings for API and frontend consumption."""
    return {
        "project_name": PROJECT_NAME,
        "project_short_name": PROJECT_SHORT_NAME,
        "project_slug": PROJECT_SLUG,
        "tagline": TAGLINE,
        "owner_name": OWNER_NAME,
        "founder_name": FOUNDER_NAME,
        "company_url": COMPANY_URL,
        "positioning": POSITIONING,
        "license_name": LICENSE_NAME,
        "support_email": SUPPORT_EMAIL,
        "repo_url": REPO_URL,
        "version": VERSION,
        "max_upload_size_bytes": MAX_UPLOAD_SIZE_BYTES,
        "job_retention_minutes": JOB_RETENTION_MINUTES,
        "analytics_enabled": ANALYTICS_ENABLED,
    }
