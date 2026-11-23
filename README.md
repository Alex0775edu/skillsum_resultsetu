# Universal Bulk Result Processing Web Application

An open-source bulk academic result downloader and reporting platform. This tool converts manual marksheet lookup into a modern bulk automation pipeline for colleges, polytechnics, and universities.

---

## Key Features

- **No Accounts & No Subscriptions**: 100% free, runs locally or on your server without logins, fees, or remote database tracking.
- **Pluggable Connector Architecture**: Adapters for different university portals (BTEUP, Standard Semester Portals, and extensible custom connectors).
- **Intelligent Excel Upload**:
  - Supports `.xlsx` and `.xls`.
  - Automatic column recognition for enrollment numbers, roll numbers, DOB, and student names.
  - Interactive column re-mapping fallback if column names vary.
  - Pre-flight validation with deduplication and empty record detection.
- **Flexible Extraction Options**:
  - Theory, practical, internal/sessional marks, and subject totals.
  - Overall percentages and dynamic pass/fail evaluations.
  - Complete PDF marksheet downloads.
- **Live Progress & Streaming Results**: Real-time progress bar, counters, live status feed, and instant retry for failed records.
- **Comprehensive Dynamic Exports**:
  - Consolidated Master Excel workbook (`.xlsx`).
  - Subject-Wise Excel workbook with dedicated tabs per subject.
  - Marksheets ZIP bundle.
  - Complete Results Package ZIP bundle.

---

## Project Structure

```
bteup_result_downloader_tool/
├── connectors/               # Modular portal adapters
│   ├── base.py              # BaseConnector, StudentResult, SubjectMarks
│   ├── bteup_connector.py   # BTEUP automation & CDP PDF capture
│   ├── demo_connector.py    # Reference demo college connector
│   └── registry.py          # Portal registry & URL matching
├── engine/                  # Core processing engine
│   ├── excel_parser.py      # Column auto-detect & validator
│   ├── exporter.py          # Dynamic Excel & ZIP packager
│   └── processor.py         # Background worker & retry queue
├── static/                  # Responsive web frontend
│   ├── css/style.css        # Modern responsive design
│   ├── js/app.js            # Real-time dashboard logic
│   └── index.html           # Single-page interface
├── app.py                   # FastAPI web application server
├── result.py                # Preserved CLI runner
├── sample_students.xlsx     # Starter student template
├── requirements.txt         # Python dependencies
├── .gitignore               # Git ignore configuration
└── LICENSE                  # MIT License
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.9+ installed.
- Google Chrome installed (for Selenium CDP headless PDF generation).

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Web Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

### 4. Running via Command Line (CLI Mode)
The original CLI tool is preserved and available:
```bash
python result.py
```

---

## Supported Portals & Adding New Connectors

### Currently Supported
1. **BTEUP (Board of Technical Education Uttar Pradesh)**:
   - Portal: `https://result.bteexam.com/even/main/rollno.aspx`
   - Required Fields: Enrollment Number, Date of Birth.
2. **Demo University Reference Portal**:
   - URL: `https://results.university.edu/semester/exam`
   - Required Fields: Enrollment / Roll Number.
   - Ideal for instant testing, grading verification, and offline demonstrations.

### Adding a Custom Connector
Create a new file in `connectors/` inheriting from `BaseConnector`:
```python
from connectors.base import BaseConnector, StudentResult

class MyUniversityConnector(BaseConnector):
    id = "my_univ"
    name = "My University Portal"
    default_url = "https://results.myuniv.edu"
    description = "Semester results portal"
    required_fields = [{"key": "enrollment", "label": "Roll Number", "type": "text", "required": True}]

    def can_handle(self, url: str) -> bool:
        return "myuniv.edu" in url.lower()

    def fetch_result(self, portal_url, student_data, options, output_dir):
        # Implement extraction logic
        ...
```
Register your connector in `connectors/registry.py`.

---

## License

This project is licensed under the [MIT License](LICENSE).
