import os
import re
import sys
import time
from base64 import b64decode
from datetime import datetime
from typing import Optional, Dict, Any

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# ------------------------------
# Configuration
# ------------------------------
RESULT_URL = ""
INPUT_FILE = ""
RESULTS_DIR = "results"

# Accurate selectors on BTEUP page, plus generic fallbacks
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

# Keywords to auto-detect fields if structure changes
ENROLLMENT_KEYWORDS = [
    "enrollment", "enrolment", "enrollment no", "roll", "rollno", "roll no",
    "roll number", "registration", "reg", "student id", "studentid", "enr"
]
DOB_KEYWORDS = [
    "dob", "date of birth", "birth", "birthdate", "dateofbirth"
]
SUBMIT_KEYWORDS = [
    "show result", "submit", "search", "view", "show", "result", "proceed", "go"
]

# Column synonyms for Excel
COLUMN_SYNONYMS = {
    "Enrollment_Number": [
        "Enrollment_Number", "Enrollment", "Enrolment", "EnrollmentNo",
        "Enrollment No", "Enrolment No", "Roll", "RollNo", "Roll No",
        "Roll Number", "Registration", "Reg No", "RegNo", "StudentID",
        "Student Id", "Enr", "EnrNo", "Enr No", "enrollment", "rollno"
    ],
    "Date_of_Birth": [
        "Date_of_Birth", "DOB", "Date of Birth", "Birthdate", "Birth Date",
        "Birth", "DateOfBirth", "dob"
    ],
    "Name": [
        "Name", "Student Name", "Student_Name", "Candidate Name", "Candidate_Name"
    ],
}


# ------------------------------
# Helper functions
# ------------------------------

def normalize_col(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def find_column(df: pd.DataFrame, candidates) -> Optional[str]:
    normalized_map = {normalize_col(c): c for c in df.columns}
    for cand in candidates:
        key = normalize_col(cand)
        if key in normalized_map:
            return normalized_map[key]
    return None


def format_dob(value) -> Optional[str]:
    """Convert any supported date value into DD/MM/YYYY."""
    if pd.isna(value):
        return None

    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime("%d/%m/%Y")

    try:
        dt = pd.to_datetime(value, dayfirst=True, errors="coerce")
    except Exception:
        dt = None

    if dt is None or pd.isna(dt):
        return None

    return dt.strftime("%d/%m/%Y")


def find_first(driver, selectors):
    for by, value in selectors:
        try:
            elem = driver.find_element(by, value)
            if elem.is_displayed():
                return elem
        except NoSuchElementException:
            continue
    return None


def get_label_text(driver, element) -> str:
    try:
        return driver.execute_script(
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
    except Exception:
        return ""


def element_text(driver, element) -> str:
    parts = []
    for attr in ["id", "name", "placeholder", "aria-label", "title", "value"]:
        val = element.get_attribute(attr)
        if val:
            parts.append(val)
    label = get_label_text(driver, element)
    if label:
        parts.append(label)
    return " ".join(parts).lower()


def score_keywords(text: str, keywords) -> int:
    score = 0
    for kw in keywords:
        if kw in text:
            score += 1
    return score


def find_best_input(driver, keywords, prefer_date=False, prefer_number=False, exclude=None):
    exclude = exclude or []
    try:
        inputs = driver.find_elements(
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

        text = element_text(driver, el)
        score = score_keywords(text, keywords)

        el_type = (el.get_attribute("type") or "").lower()
        if prefer_date and el_type == "date":
            score += 2
        if prefer_number and el_type in ("number", "tel"):
            score += 1

        if score > best_score:
            best = el
            best_score = score

    return best


def find_best_submit(driver):
    candidates = []
    try:
        candidates.extend(driver.find_elements(By.XPATH, "//button"))
        candidates.extend(driver.find_elements(By.XPATH, "//input[@type='submit' or @type='button']"))
    except Exception:
        return None

    best = None
    best_score = 0
    for el in candidates:
        try:
            if not el.is_displayed():
                continue
        except Exception:
            continue

        text = (el.text or "").lower()
        for attr in ["id", "name", "value", "aria-label", "title"]:
            val = el.get_attribute(attr)
            if val:
                text += " " + val.lower()

        score = score_keywords(text, SUBMIT_KEYWORDS)
        if score > best_score:
            best = el
            best_score = score

    return best


def captcha_present(driver) -> bool:
    try:
        candidates = driver.find_elements(
            By.XPATH,
            "//input[contains(translate(@name,'CAPTCHA','captcha'),'captcha') or "
            "contains(translate(@id,'CAPTCHA','captcha'),'captcha')]"
        )
        return len(candidates) > 0
    except Exception:
        return False


def set_input_value(driver, element, value: str) -> None:
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
            driver.execute_script("arguments[0].value = arguments[1];", element, value)
    except Exception:
        pass


def dismiss_datepicker(driver) -> None:
    try:
        driver.execute_script(
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


def safe_click(driver, element) -> bool:
    try:
        element.click()
        return True
    except Exception:
        pass

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception:
        pass

    try:
        driver.execute_script(
            "arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));",
            element,
        )
        return True
    except Exception:
        return False


def save_pdf(driver, filepath: str) -> bool:
    try:
        pdf = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "preferCSSPageSize": True,
        })
        with open(filepath, "wb") as f:
            f.write(b64decode(pdf["data"]))
        return True
    except Exception:
        return False


def safe_filename(text: str) -> str:
    return "".join(ch for ch in text if ch.isalnum() or ch in ("_", "-"))


def dismiss_any_alert(driver) -> Optional[str]:
    """Dismiss any unexpected or hanging modal alert and return its text."""
    try:
        alert = driver.switch_to.alert
        text = alert.text
        alert.accept()
        return text
    except Exception:
        return None


def extract_marksheet_info(driver) -> Dict[str, str]:
    """Extract student details and result info from the marksheet page text."""
    info = {
        "Student_Name": "",
        "Father_Name": "",
        "Branch": "",
        "Grand_Total": "",
        "Result": "",
    }
    try:
        body = driver.find_element(By.TAG_NAME, "body").text
        
        m_name = re.search(r"STUDENT\s+NAME\s*[:\s]\s*([A-Z\s]+?)(?:\s+FATHER\s+NAME|\n|$)", body, re.IGNORECASE)
        if m_name:
            info["Student_Name"] = " ".join(m_name.group(1).split())

        m_father = re.search(r"FATHER\s+NAME\s*[:\s]\s*([A-Z\s]+?)(?:\s+ENROLLMENT|\n|$)", body, re.IGNORECASE)
        if m_father:
            info["Father_Name"] = " ".join(m_father.group(1).split())

        m_branch = re.search(r"BRANCH\s+NAME\s*[:\s]\s*([^\n]+)", body, re.IGNORECASE)
        if m_branch:
            info["Branch"] = " ".join(m_branch.group(1).split())

        m_total = re.search(r"GRAND\s+TOTAL\s*[:\s]\s*([\d\s/]+)", body, re.IGNORECASE)
        if m_total:
            info["Grand_Total"] = " ".join(m_total.group(1).split())

        m_result = re.search(r"RESULT\s+([A-Z\s]+?)(?:DISCLAIMER|\n|$)", body, re.IGNORECASE)
        if m_result:
            info["Result"] = " ".join(m_result.group(1).split())

    except Exception:
        pass
    return info


# ------------------------------
# Main script
# ------------------------------

def main():
    print("=" * 60)
    print("       BTEUP Result Auto Downloader & Exporter")
    print("=" * 60)

    force_download = "--force" in sys.argv or "--overwrite" in sys.argv
    headless = "--visible" not in sys.argv and "--head" not in sys.argv

    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: '{INPUT_FILE}' not found in the project folder.")
        sys.exit(1)

    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as exc:
        print(f"ERROR: Failed to read '{INPUT_FILE}': {exc}")
        sys.exit(1)

    enrollment_col = find_column(df, COLUMN_SYNONYMS["Enrollment_Number"])
    dob_col = find_column(df, COLUMN_SYNONYMS["Date_of_Birth"])
    name_col = find_column(df, COLUMN_SYNONYMS["Name"])

    if not enrollment_col or not dob_col:
        print("ERROR: Required columns not found.")
        print("Found columns:", ", ".join([str(c) for c in df.columns]))
        print("Need Enrollment and Date of Birth columns.")
        sys.exit(1)

    rename_map = {
        enrollment_col: "Enrollment_Number",
        dob_col: "Date_of_Birth",
    }
    if name_col:
        rename_map[name_col] = "Name"
    df = df.rename(columns=rename_map)
    if "Name" not in df.columns:
        df["Name"] = ""

    os.makedirs(RESULTS_DIR, exist_ok=True)

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    else:
        chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    total = len(df)
    success_count = 0
    skipped_count = 0
    failed_count = 0
    records_summary = []

    print(f"Found {total} students in '{INPUT_FILE}'.")
    print(f"Output directory: '{RESULTS_DIR}'")
    print(f"Running mode: {'Headless' if headless else 'Visible'}")
    print("-" * 60)

    for idx, row in df.iterrows():
        enrollment = str(row["Enrollment_Number"]).strip()
        raw_dob = row["Date_of_Birth"]
        dob = format_dob(raw_dob)

        student_info = {
            "Enrollment": enrollment,
            "DOB": dob or str(raw_dob),
            "Student_Name": "",
            "Father_Name": "",
            "Branch": "",
            "Grand_Total": "",
            "Result": "",
            "Status": "Pending",
            "PDF_File": "",
        }

        print(f"[{idx + 1:02d}/{total:02d}] Enrollment: {enrollment} (DOB: {dob})...", end=" ", flush=True)

        if not enrollment or enrollment.lower() == "nan":
            print("[SKIPPED - Empty enrollment]")
            student_info["Status"] = "Skipped (Empty enrollment)"
            records_summary.append(student_info)
            failed_count += 1
            continue

        if not dob:
            print(f"[SKIPPED - Invalid DOB: '{raw_dob}']")
            student_info["Status"] = f"Skipped (Invalid DOB: {raw_dob})"
            records_summary.append(student_info)
            failed_count += 1
            continue

        base_name = safe_filename(enrollment)
        pdf_path = os.path.join(RESULTS_DIR, f"{base_name}.pdf")

        if not force_download and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
            print(f"[ALREADY EXISTS] -> {pdf_path}")
            student_info["Status"] = "Success (Cached)"
            student_info["PDF_File"] = pdf_path
            records_summary.append(student_info)
            skipped_count += 1
            continue

        # Dismiss any leftover alert from previous iteration
        dismiss_any_alert(driver)

        try:
            driver.get(RESULT_URL)
            dismiss_datepicker(driver)

            # Locate elements
            enrollment_input = find_first(driver, ENROLLMENT_SELECTORS)
            if not enrollment_input:
                enrollment_input = find_best_input(driver, ENROLLMENT_KEYWORDS, prefer_number=True)

            dob_input = find_first(driver, DOB_SELECTORS)
            if not dob_input:
                dob_input = find_best_input(driver, DOB_KEYWORDS, prefer_date=True, exclude=[enrollment_input] if enrollment_input else [])

            submit_button = find_first(driver, SUBMIT_SELECTORS)
            if not submit_button:
                submit_button = find_best_submit(driver)

            if not enrollment_input or not dob_input or not submit_button:
                print("[ERROR - Form inputs not found]")
                student_info["Status"] = "Error (Form inputs not found)"
                records_summary.append(student_info)
                failed_count += 1
                continue

            set_input_value(driver, enrollment_input, enrollment)
            set_input_value(driver, dob_input, dob)
            dismiss_datepicker(driver)

            if captcha_present(driver):
                print("\n  [CAPTCHA] Please solve captcha in browser, then press ENTER...")
                input()
            else:
                time.sleep(0.2)

            if not safe_click(driver, submit_button):
                print("[ERROR - Submit button click failed]")
                student_info["Status"] = "Error (Submit button click failed)"
                records_summary.append(student_info)
                failed_count += 1
                continue

            # Poll for alert or page navigation away from rollno.aspx
            start_time = time.time()
            alert_msg = None
            navigated = False

            while time.time() - start_time < 12:
                # 1. Check if an alert was triggered
                alert_msg = dismiss_any_alert(driver)
                if alert_msg:
                    break

                # 2. Check if navigated away from search form
                try:
                    curr_url = driver.current_url.lower()
                    if "rollno.aspx" not in curr_url and (".aspx" in curr_url or "result" in curr_url):
                        navigated = True
                        break
                except Exception:
                    # In case current_url triggers UnexpectedAlertPresentException
                    alert_msg = dismiss_any_alert(driver)
                    if alert_msg:
                        break

                time.sleep(0.2)

            if alert_msg:
                print(f"[NO RECORD FOUND - {alert_msg}]")
                student_info["Status"] = f"Not Found ({alert_msg})"
                records_summary.append(student_info)
                failed_count += 1
                continue

            if not navigated:
                print("[TIMEOUT - Result page did not load]")
                student_info["Status"] = "Timeout"
                records_summary.append(student_info)
                failed_count += 1
                continue

            # Wait for document ready
            try:
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            except TimeoutException:
                pass

            time.sleep(0.5)

            # Extract marksheet details
            marksheet_info = extract_marksheet_info(driver)
            student_info.update(marksheet_info)

            # Save result PDF
            if save_pdf(driver, pdf_path):
                student_info["Status"] = "Success"
                student_info["PDF_File"] = pdf_path
                name_str = f" ({student_info['Student_Name']})" if student_info['Student_Name'] else ""
                print(f"[DOWNLOADED]{name_str} -> {pdf_path}")
                success_count += 1
            else:
                png_path = os.path.join(RESULTS_DIR, f"{base_name}.png")
                driver.save_screenshot(png_path)
                student_info["Status"] = "Success (Screenshot PNG)"
                student_info["PDF_File"] = png_path
                print(f"[DOWNLOADED PNG] -> {png_path}")
                success_count += 1

            records_summary.append(student_info)

        except Exception as exc:
            dismiss_any_alert(driver)
            print(f"[EXCEPTION: {exc}]")
            student_info["Status"] = f"Error: {exc}"
            records_summary.append(student_info)
            failed_count += 1
            continue

    driver.quit()

    # Save summary report to Excel
    summary_path = os.path.join(RESULTS_DIR, "results_summary.xlsx")
    try:
        summary_df = pd.DataFrame(records_summary)
        summary_df.to_excel(summary_path, index=False)
        print("-" * 60)
        print(f"Summary report saved to: {summary_path}")
    except Exception as exc:
        print(f"Failed to save summary report: {exc}")

    print("=" * 60)
    print("Download Summary:")
    print(f"  Total Processed: {total}")
    print(f"  Successfully Downloaded: {success_count}")
    print(f"  Already Existed: {skipped_count}")
    print(f"  Not Found / Failed: {failed_count}")
    
    missing = [r for r in records_summary if r["Status"] not in ("Success", "Success (Cached)", "Success (Screenshot PNG)")]
    if missing:
        print("\nStudents not retrieved:")
        for m in missing:
            print(f"  - Enrollment: {m['Enrollment']}, DOB: {m['DOB']}, Reason: {m['Status']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
