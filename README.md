# SkillSum ResultSetu

> **Simplify bulk academic result processing.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

**SkillSum ResultSetu** is an independent, free, and open-source academic result processing and marksheet extraction platform developed by **SkillSum Innovations**. It converts tedious manual marksheet queries into an automated bulk extraction pipeline for colleges, polytechnics, department heads, and educational administrators.

---

## 🌟 Key Highlights

- **100% Free & Open Source**: MIT Licensed with no subscriptions, paid APIs, user registration, accounts, or payment gates.
- **Privacy-First Architecture**: Excel student spreadsheets are parsed locally inside the client browser. No persistent database of student records is maintained.
- **Pluggable Connector Architecture**: Modular adapter pattern allowing custom university portals (e.g., BTEUP, standard semester portals) to be connected cleanly without altering the core engine.
- **Comprehensive Dynamic Exports**:
  - **Consolidated Master Excel (`.xlsx`)**: Formatted master spreadsheet with student details, evaluated subjects, and dynamic totals.
  - **Subject-Wise Excel (`.xlsx`)**: Dedicated workbook tabs per subject displaying Theory, Practical, and Sessional components.
  - **Marksheets Archive (`.zip`)**: Compressed bundle of all downloaded student marksheet PDFs.
  - **Complete Package (`.zip`)**: Consolidated Excel, Subject-wise sheets, marksheets folder, and summary report.
- **Real-Time Progress & Retry**: Live progress bar, counters, privacy-masked terminal logs, and single-click retry for failed queries.
- **Security & Integrity**: Built-in SSRF guards, path traversal sanitizers, 5MB upload size limits, and a 30-minute automated Time-To-Live (TTL) temporary file purge.

---

## 🏗 System Architecture

```
skillsum-resultsetu/
├── connectors/               # Pluggable university portal connectors
│   ├── base.py              # BaseConnector, StudentResult, SubjectMarks
│   ├── bteup_connector.py   # BTEUP automation & CDP PDF capture
│   ├── demo_connector.py    # Reference demo college connector
│   └── registry.py          # Portal registry & SSRF-protected URL matching
├── engine/                  # Core processing engine
│   ├── excel_parser.py      # Column auto-detect (.xlsx/.xls) & deduplication
│   ├── exporter.py          # Dynamic OpenPyXL & zipfile exporters
│   ├── processor.py         # Threaded worker with 30-min TTL cleaner
│   └── security.py          # SSRF protection, path traversal sanitization
├── static/                  # Responsive web frontend (Deep Green / Light Green)
│   ├── css/style.css        # Responsive, accessible mobile-first styling
│   ├── js/app.js            # SPA routing & real-time live streaming
│   ├── js/vendor/           # Self-contained offline client parsing (xlsx.full.min.js)
│   └── index.html           # 12 integrated pages & SVG brand mark
├── app.py                   # FastAPI web application server
├── brand_config.py          # Centralized branding & configuration module
├── result.py                # Preserved CLI runner
├── sample_students.xlsx     # Sample Excel template
├── requirements.txt         # Python dependencies
├── .env.example             # Environment configuration template
├── vercel.json              # Vercel deployment configuration
├── .gitignore               # Git ignore configuration
├── LICENSE                  # MIT License
└── test_suite.py            # Comprehensive automated test suite
```

---

## 🔒 Privacy & Data Flow

```
[User Excel File (.xlsx / .xls)]
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT BROWSER                         │
│  1. Read ArrayBuffer via FileReader                         │
│  2. Local parsing using static/js/vendor/xlsx.full.min.js   │
│  3. Detect columns (Enrollment, DOB, Name) via synonyms     │
│  4. Calculate total rows, empty rows, duplicate rows        │
│  5. Render 10-row preview table inside browser RAM          │
│  * The original Excel spreadsheet is NEVER uploaded *       │
└─────────────────────────────────────────────────────────────┘
             │ Only validated query rows transmitted
             │ via POST /api/process/start_direct
             ▼
┌─────────────────────────────────────────────────────────────┐
│                      SERVER BACKEND                         │
│  1. Validate URL against SSRF (blocks private/loopback IPs) │
│  2. Route query to matching portal connector                │
│  3. Query portal via headless browser & CDP printToPDF      │
│  4. Extract subject marks from marksheet DOM                │
│  5. Generate Consolidated & Subject-wise XLSX (OpenPyXL)    │
│  6. Package into ZIP archives in temp_storage/{job_id}/     │
└─────────────────────────────────────────────────────────────┘
             │
             ▼
[User Downloads: XLSX / PDF / ZIP]
             │
      (After 30 minutes)
             │
             ▼
[Automatic TTL Purge deletes temp_storage/{job_id}/ from disk]
```

### Privacy Guarantees
1. **Zero Tracking**: No Google Analytics, cookies, advertising trackers, or external telemetry scripts.
2. **Masked Logs**: Application logs privacy-mask student roll numbers (e.g. `...4001`) and never record student names or marks in console logs.
3. **Automated Deletion**: Temporary session directories in `temp_storage/` are purged after 30 minutes by a background cleaner thread.
4. **No Permanent Database**: Operates entirely in-memory and volatile storage.

---

## 🚀 Installation & Local Development

### Prerequisites
- Python 3.9 or higher.
- Google Chrome (for Selenium CDP headless marksheet PDF capture).

### 1. Clone the Repository
```bash
git clone https://github.com/Alex0775edu/skillsum_resultsetu.git
cd skillsum_resultsetu
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Web Application
```bash
python app.py
```
Open **`http://127.0.0.1:8000`** in your browser to launch the dashboard.

### 5. Running in Command-Line Mode (CLI)
The original CLI automation remains fully operational:
```bash
python result.py
```

### 6. Run the Automated Test Suite
```bash
python -m unittest test_suite.py
```

---

## 🌐 Supported Universities & Portals

1. **Board of Technical Education Uttar Pradesh (BTEUP)**:
   - Portal: `https://result.bteexam.com/even/main/rollno.aspx`
   - Required Fields: Enrollment Number, Date of Birth.
2. **Standard University Demo Portal**:
   - URL: `https://results.university.edu/semester/exam`
   - Required Fields: Enrollment / Roll Number.
   - Purpose: Multi-subject reference portal for testing, evaluation, and grading verification.

### Adding a New University Connector
Create an adapter in `connectors/` inheriting from `BaseConnector`:
```python
from connectors.base import BaseConnector, StudentResult

class CustomUniversityConnector(BaseConnector):
    id = "custom_univ"
    name = "Custom University Examination Portal"
    default_url = "https://results.customuniv.edu"
    description = "Semester results portal"
    required_fields = [
        {"key": "enrollment", "label": "Roll Number", "type": "text", "required": True}
    ]

    def can_handle(self, url: str) -> bool:
        return "customuniv.edu" in url.lower()

    def fetch_result(self, portal_url, student_data, options, output_dir):
        # Implement extraction logic
        ...
```
Register your connector in `connectors/registry.py`.

---

## ☁️ Deployment & Vercel Readiness

A [`vercel.json`](vercel.json) configuration is included for deploying the API routes and static frontend to Vercel Serverless Functions.

### Important Architectural Notice on Serverless Deployment
- **Client-Side Parsing & Static Web UI**: Runs on Vercel with zero cold-start delay.
- **REST API Endpoints**: Validation, column mapping, configuration, and sample template downloads execute as standard Vercel serverless functions.
- **Selenium / Headless Chrome Processing**:
  - Vercel Serverless Functions run in lightweight AWS Lambda containers with standard execution timeouts (10 seconds on Hobby, up to 60 seconds on Pro) and **do not** include a pre-installed Google Chrome or ChromeDriver binary by default.
  - **Recommended Production Deployment for Heavy Scraping**: Run the backend processing engine on a long-running container or virtual server (e.g. Docker, Railway, Render, Fly.io, or AWS EC2) where Google Chrome is installed, or point Selenium to a remote WebDriver service (e.g. Browserless).
  - *The project preserves its full Selenium engine and does not degrade functionality with mock data.*

---

## 📄 License & Attribution

- **License**: Released under the [MIT License](LICENSE).
- **Ownership**: Independent open-source project by **SkillSum Innovations**.
- **Support**: For inquiries, contact `[SUPPORT_EMAIL_PLACEHOLDER]`.
- **Disclaimer**: This is an independent utility not affiliated with, endorsed by, or an official product of any university, college, or examination board.
