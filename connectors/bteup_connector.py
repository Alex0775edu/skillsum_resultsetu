"""
BTEUP (Board of Technical Education Uttar Pradesh) Result Portal Connector.
Preserves all functionality of the original result.py automation while cleanly
adapting to the BaseConnector interface.
"""
import os
import re
import time
from base64 import b64decode
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from .base import BaseConnector, StudentResult, SubjectMarks


class BTEUPConnector(BaseConnector):
    """Connector for BTEUP result website."""

    id = "bteup"
    name = "Board of Technical Education Uttar Pradesh (BTEUP)"
    default_url = "https://result.bteexam.com/even/main/rollno.aspx"
    description = (
        "Supports BTEUP semester & annual diploma examination result portals. "
        "Requires Student Enrollment Number and Date of Birth (DD/MM/YYYY)."
    )

    required_fields = [
        {
            "key": "enrollment",
            "label": "Enrollment Number",
            "type": "text",
            "required": True,
            "synonyms": [
                "enrollment", "enrolment", "enrollment_no", "enrollment no",
                "roll", "rollno", "roll no", "roll number", "reg_no", "regno",
                "student_id", "enr", "enr_no"
            ]
        },
        {
            "key": "dob",
            "label": "Date of Birth (DD/MM/YYYY)",
            "type": "date",
            "required": True,
            "synonyms": [
                "dob", "date_of_birth", "date of birth", "birthdate", "birth date",
                "birth", "dateofbirth"
            ]
        },
        {
            "key": "name",
            "label": "Student Name (Optional)",
            "type": "text",
            "required": False,
            "synonyms": ["name", "student_name", "student name", "candidate_name"]
        }
    ]

    ENROLLMENT_SELECTORS = [
        (By.ID, "txtRollNo"),
        (By.NAME, "txtRollNo"),
        (By.NAME, "enrollment"),
        (By.ID, "enrollment"),
        (By.NAME, "rollno"),
        (By.ID, "rollno"),
    ]
    DOB_SELECTORS = [
        (By.ID, "txt_dob"),
        (By.NAME, "txt_dob"),
        (By.NAME, "dob"),
        (By.ID, "dob"),
    ]
    SUBMIT_SELECTORS = [
        (By.ID, "btnSave"),
        (By.NAME, "btnSave"),
        (By.ID, "submit"),
        (By.NAME, "submit"),
        (By.XPATH, "//button[@type='submit']"),
        (By.XPATH, "//input[@type='submit']"),
    ]

    ENROLLMENT_KEYWORDS = [
        "enrollment", "enrolment", "enrollment no", "roll", "rollno", "roll no",
        "roll number", "registration", "reg", "student id", "studentid", "enr"
    ]
    DOB_KEYWORDS = ["dob", "date of birth", "birth", "birthdate", "dateofbirth"]
    SUBMIT_KEYWORDS = ["show result", "submit", "search", "view", "show", "result", "proceed", "go"]

    def __init__(self, headless: bool = True):
        self._headless = headless
        self._driver: Optional[webdriver.Chrome] = None

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        clean_url = url.lower().strip()
        return any(k in clean_url for k in [
            "bteexam.com", "bteup.ac.in", "bteup.org", "bteup", "rollno.aspx"
        ])

    def initialize(self) -> None:
        if self._driver is not None:
            return

        chrome_options = Options()
        if self._headless:
            chrome_options.add_argument("--headless=new")
        else:
            chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Suppress logging
        chrome_options.add_argument("--log-level=3")

        self._driver = webdriver.Chrome(options=chrome_options)
        self._driver.set_page_load_timeout(30)

    def cleanup(self) -> None:
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    # --- Preserved helper methods from result.py ---

    @staticmethod
    def format_dob(value: Any) -> Optional[str]:
        if pd.isna(value) or value is None:
            return None
        if isinstance(value, (datetime, pd.Timestamp)):
            return value.strftime("%d/%m/%Y")
        try:
            dt = pd.to_datetime(value, dayfirst=True, errors="coerce")
            if dt is not None and not pd.isna(dt):
                return dt.strftime("%d/%m/%Y")
        except Exception:
            pass
        val_str = str(value).strip()
        return val_str if val_str else None

    @staticmethod
    def safe_filename(text: str) -> str:
        return "".join(ch for ch in str(text) if ch.isalnum() or ch in ("_", "-"))

    def _dismiss_any_alert(self) -> Optional[str]:
        try:
            alert = self._driver.switch_to.alert
            text = alert.text
            alert.accept()
            return text
        except Exception:
            return None

    def _dismiss_datepicker(self) -> None:
        try:
            self._driver.execute_script(
                """
                const selectors = [
                    '.datepicker', '.datepicker-days', '.ui-datepicker',
                    '.datetimepicker', '.day', '.modal-backdrop'
                ];
                for (const sel of selectors) {
                    document.querySelectorAll(sel).forEach(el => {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.remove();
                    });
                }
                """
            )
        except Exception:
            pass

    def _find_first(self, selectors):
        for by, value in selectors:
            try:
                elem = self._driver.find_element(by, value)
                if elem.is_displayed():
                    return elem
            except NoSuchElementException:
                continue
        return None

    def _element_text(self, element) -> str:
        parts = []
        for attr in ["id", "name", "placeholder", "aria-label", "title", "value"]:
            val = element.get_attribute(attr)
            if val:
                parts.append(val)
        try:
            label = self._driver.execute_script(
                """
                const el = arguments[0];
                let text = "";
                if (el.labels && el.labels.length) {
                    text = Array.from(el.labels).map(l => l.innerText).join(" ");
                }
                if (!text) {
                    const wrap = el.closest('label');
                    if (wrap) text = wrap.innerText;
                }
                return text || "";
                """,
                element,
            )
            if label:
                parts.append(label)
        except Exception:
            pass
        return " ".join(parts).lower()

    def _find_best_input(self, keywords, prefer_date=False, prefer_number=False, exclude=None):
        exclude = exclude or []
        try:
            inputs = self._driver.find_elements(
                By.XPATH,
                "//input[not(@type) or @type='text' or @type='tel' or @type='number' or @type='date']"
            )
        except Exception:
            return None

        best = None
        best_score = 0
        for el in inputs:
            try:
                if exclude and el in exclude:
                    continue
                if not el.is_displayed():
                    continue
            except Exception:
                continue

            text = self._element_text(el)
            score = 0
            for kw in keywords:
                if kw in text:
                    score += 1

            el_type = (el.get_attribute("type") or "").lower()
            if prefer_date and el_type == "date":
                score += 2
            if prefer_number and el_type in ("number", "tel"):
                score += 1

            if score > best_score:
                best = el
                best_score = score
        return best

    def _find_best_submit(self):
        candidates = []
        try:
            candidates.extend(self._driver.find_elements(By.XPATH, "//button"))
            candidates.extend(self._driver.find_elements(By.XPATH, "//input[@type='submit' or @type='button']"))
        except Exception:
            return None

        best = None
        best_score = 0
        for el in candidates:
            try:
                if not el.is_displayed():
                    continue
                text = (el.text or "").lower()
                for attr in ["id", "name", "value", "aria-label", "title"]:
                    val = el.get_attribute(attr)
                    if val:
                        text += " " + val.lower()

                score = sum(1 for kw in self.SUBMIT_KEYWORDS if kw in text)
                if score > best_score:
                    best = el
                    best_score = score
            except Exception:
                continue
        return best

    def _set_input_value(self, element, value: str) -> None:
        try:
            element.clear()
        except Exception:
            pass
        try:
            element.send_keys(value)
        except Exception:
            pass
        try:
            current = element.get_attribute("value") or ""
            if current.strip() != value.strip():
                self._driver.execute_script("arguments[0].value = arguments[1];", element, value)
        except Exception:
            pass

    def _safe_click(self, element) -> bool:
        try:
            element.click()
            return True
        except Exception:
            pass
        try:
            self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.2)
            self._driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            pass
        try:
            self._driver.execute_script(
                "arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));",
                element,
            )
            return True
        except Exception:
            return False

    def _save_pdf(self, filepath: str) -> bool:
        try:
            pdf = self._driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,
                "preferCSSPageSize": True,
            })
            with open(filepath, "wb") as f:
                f.write(b64decode(pdf["data"]))
            return True
        except Exception:
            return False

    def _extract_marksheet_data(self) -> Dict[str, Any]:
        """Extract structured information and subject rows from the rendered page."""
        data = {
            "Student_Name": "",
            "Father_Name": "",
            "Branch": "",
            "Institute": "",
            "Grand_Total": "",
            "Result": "",
            "Subjects": []
        }
        try:
            body = self._driver.find_element(By.TAG_NAME, "body").text
            m_name = re.search(r"STUDENT\s+NAME\s*[:\s]\s*([A-Z\s]+?)(?:\s+FATHER\s+NAME|\n|$)", body, re.IGNORECASE)
            if m_name:
                data["Student_Name"] = " ".join(m_name.group(1).split())

            m_father = re.search(r"FATHER\s+NAME\s*[:\s]\s*([A-Z\s]+?)(?:\s+ENROLLMENT|\n|$)", body, re.IGNORECASE)
            if m_father:
                data["Father_Name"] = " ".join(m_father.group(1).split())

            m_branch = re.search(r"BRANCH\s+NAME\s*[:\s]\s*([^\n]+)", body, re.IGNORECASE)
            if m_branch:
                data["Branch"] = " ".join(m_branch.group(1).split())

            m_inst = re.search(r"INSTITUTE\s+NAME\s*[:\s]\s*([^\n]+)", body, re.IGNORECASE)
            if m_inst:
                data["Institute"] = " ".join(m_inst.group(1).split())

            m_total = re.search(r"GRAND\s+TOTAL\s*[:\s]\s*([\d\s/]+)", body, re.IGNORECASE)
            if m_total:
                data["Grand_Total"] = " ".join(m_total.group(1).split())

            m_result = re.search(r"RESULT\s+([A-Z\s]+?)(?:DISCLAIMER|\n|$)", body, re.IGNORECASE)
            if m_result:
                data["Result"] = " ".join(m_result.group(1).split())

            # Attempt to extract subject marks table if present
            tables = self._driver.find_elements(By.TAG_NAME, "table")
            for tbl in tables:
                rows = tbl.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cols = [c.text.strip() for c in row.find_elements(By.TAG_NAME, "td")]
                    if len(cols) >= 4 and any(ch.isdigit() for ch in "".join(cols)):
                        # Typical format: [Code, Subject Name, Max/Theory, Obtained, ...]
                        code = cols[0] if len(cols[0]) <= 8 else ""
                        name = cols[1] if code else cols[0]
                        # Look for numeric marks in columns
                        nums = []
                        for val in cols:
                            try:
                                nums.append(float(val))
                            except ValueError:
                                pass
                        if nums:
                            subj = SubjectMarks(
                                code=code,
                                name=name,
                                total_obtained=nums[-1] if nums else None,
                                total_max=nums[-2] if len(nums) >= 2 else None,
                                status="PASS"
                            )
                            data["Subjects"].append(subj)
        except Exception:
            pass
        return data

    def fetch_result(
        self,
        portal_url: str,
        student_data: Dict[str, Any],
        options: Dict[str, Any],
        output_dir: str,
    ) -> StudentResult:
        """Fetch result for one student using Selenium headless browser."""
        self.initialize()
        enrollment = str(student_data.get("enrollment") or "").strip()
        raw_dob = student_data.get("dob")
        dob = self.format_dob(raw_dob)

        result = StudentResult(
            enrollment=enrollment,
            student_name=str(student_data.get("name") or "").strip(),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if not enrollment or enrollment.lower() == "nan":
            result.status = "Skipped"
            result.error_message = "Empty enrollment number"
            return result

        if not dob:
            result.status = "Skipped"
            result.error_message = f"Invalid or missing Date of Birth: '{raw_dob}'"
            return result

        base_name = self.safe_filename(enrollment)
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

        # Check existing cache if force_download is not set
        if not options.get("force_download", False) and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
            result.status = "Cached"
            result.pdf_path = pdf_path
            return result

        target_url = portal_url.strip() if portal_url else self.default_url

        try:
            self._dismiss_any_alert()
            self._driver.get(target_url)
            self._dismiss_datepicker()

            enrollment_input = self._find_first(self.ENROLLMENT_SELECTORS)
            if not enrollment_input:
                enrollment_input = self._find_best_input(self.ENROLLMENT_KEYWORDS, prefer_number=True)

            dob_input = self._find_first(self.DOB_SELECTORS)
            if not dob_input:
                dob_input = self._find_best_input(
                    self.DOB_KEYWORDS, prefer_date=True, exclude=[enrollment_input] if enrollment_input else []
                )

            submit_button = self._find_first(self.SUBMIT_SELECTORS)
            if not submit_button:
                submit_button = self._find_best_submit()

            if not enrollment_input or not dob_input or not submit_button:
                result.status = "Failed"
                result.error_message = "Form input elements (Enrollment / DOB / Submit) not found on portal page."
                return result

            self._set_input_value(enrollment_input, enrollment)
            self._set_input_value(dob_input, dob)
            self._dismiss_datepicker()

            time.sleep(0.3)

            if not self._safe_click(submit_button):
                result.status = "Failed"
                result.error_message = "Failed to submit result request form."
                return result

            # Poll for alert or navigation away
            start_time = time.time()
            alert_msg = None
            navigated = False

            while time.time() - start_time < 12:
                alert_msg = self._dismiss_any_alert()
                if alert_msg:
                    break
                try:
                    curr_url = self._driver.current_url.lower()
                    if "rollno.aspx" not in curr_url and (".aspx" in curr_url or "result" in curr_url):
                        navigated = True
                        break
                except Exception:
                    alert_msg = self._dismiss_any_alert()
                    if alert_msg:
                        break
                time.sleep(0.2)

            if alert_msg:
                result.status = "Failed"
                result.error_message = f"Portal returned notice: {alert_msg}"
                return result

            if not navigated:
                result.status = "Failed"
                result.error_message = "Request timed out or portal did not navigate to result sheet."
                return result

            # Wait for readyState
            try:
                WebDriverWait(self._driver, 8).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                pass

            time.sleep(0.5)

            # Extract marksheet details
            extracted = self._extract_marksheet_data()
            if extracted.get("Student_Name"):
                result.student_name = extracted["Student_Name"]
            result.father_name = extracted.get("Father_Name", "")
            result.branch = extracted.get("Branch", "")
            result.institute = extracted.get("Institute", "")
            result.result_status = extracted.get("Result", "PASS")
            result.subjects = extracted.get("Subjects", [])

            # Grand Total parse
            raw_gt = extracted.get("Grand_Total", "")
            if "/" in raw_gt:
                parts = raw_gt.split("/")
                try:
                    result.total_obtained = float(re.sub(r"[^\d.]", "", parts[0]))
                    result.total_max = float(re.sub(r"[^\d.]", "", parts[1]))
                    if result.total_max > 0:
                        result.overall_percentage = round((result.total_obtained / result.total_max) * 100, 2)
                except Exception:
                    pass

            # Save PDF marksheet if requested
            if options.get("download_pdf", True):
                os.makedirs(output_dir, exist_ok=True)
                if self._save_pdf(pdf_path):
                    result.pdf_path = pdf_path
                else:
                    # Screenshot fallback
                    png_path = os.path.join(output_dir, f"{base_name}.png")
                    self._driver.save_screenshot(png_path)
                    result.pdf_path = png_path

            result.status = "Success"
            return result

        except WebDriverException as we:
            self._dismiss_any_alert()
            result.status = "Failed"
            result.error_message = f"Web driver connection error: {str(we)[:120]}"
            return result
        except Exception as ex:
            self._dismiss_any_alert()
            result.status = "Failed"
            result.error_message = f"Unexpected processing error: {str(ex)[:120]}"
            return result
