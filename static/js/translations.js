// SkillSum ResultSetu - Bilingual Translation Dictionary (English + Hindi)

const TRANSLATIONS = {
  en: {
    // Navigation
    nav_home: "Home",
    nav_how_it_works: "How It Works",
    nav_universities: "Supported Universities",
    nav_faq: "FAQ",
    nav_contact: "Contact",
    nav_process: "Process Results",
    nav_history: "Local History",

    // Hero
    hero_badge: "✓ 100% Free & Open Source • MIT License",
    hero_tagline: "Simplify bulk academic result processing.",
    hero_launch_btn: "🚀 Launch Bulk Processing",
    hero_learn_btn: "Learn How It Works",

    // Step 1
    step1_title: "Select Result Portal",
    step1_desc: "Enter college or university examination portal URL",
    step1_input_label: "Result Portal URL",
    step1_validate_btn: "Validate Portal",
    step1_quick_title: "Quick Select:",
    step1_bteup_btn: "BTEUP Official Portal",
    step1_demo_btn: "Standard University (Demo & Testing)",

    // Step 2
    step2_title: "Upload Student List (Excel)",
    step2_desc: "Processed locally in your browser",
    step2_drop_text: "Drag & drop your student Excel file here, or click to browse",
    step2_drop_hint: "Supports .xlsx and .xls files containing student enrollments or roll numbers",
    step2_badge_local: "🔒 Client-Side Local Parsing Enabled",
    step2_template_text: "Need a structured format template?",
    step2_template_btn: "⬇ Download Sample Excel Template",
    step2_total_rows: "Total Rows",
    step2_valid_rows: "Valid Records",
    step2_dup_rows: "Duplicate Rows",
    step2_empty_rows: "Empty Rows",
    step2_map_label: "Confirm or Map Excel Columns:",
    step2_map_enr: "Enrollment / Roll No Column *",
    step2_map_dob: "Date of Birth (DOB) Column",
    step2_map_name: "Student Name Column",
    step2_preview_title: "Student Records Preview (First 10 Rows):",

    // Step 3
    step3_title: "Configure Extraction Options",
    step3_desc: "Select desired data fields and export artifacts",
    step3_opt_all: "All Subjects",
    step3_opt_theory: "Theory Marks",
    step3_opt_practical: "Practical Marks",
    step3_opt_internal: "Internal / Sessional Marks",
    step3_opt_subject_pct: "Subject-wise Percentages",
    step3_opt_totals: "Total Marks (Obtained / Max)",
    step3_opt_percentage: "Overall Percentage (%)",
    step3_opt_status: "Pass / Fail Status",
    step3_opt_pdf: "Individual Performance PDF",
    step3_opt_force: "Force Re-download (Bypass Cache)",
    step3_start_btn: "▶ Start Bulk Processing",

    // Step 4
    step4_processing_title: "Processing Students",
    step4_cancel_btn: "⏹ Cancel Processing",
    step4_total: "Total",
    step4_success: "Success",
    step4_failed: "Failed",
    step4_skipped: "Skipped",
    step4_stream_title: "Live Result Stream:",
    step4_retry_failed_btn: "🔄 Retry All Failed",

    // Step 5
    step5_title: "Export & Download Results",
    step5_desc: "Dynamic Excel calculations & preserved original marksheets",
    step5_cons_title: "📊 Consolidated Excel",
    step5_cons_desc: "Master sheet with student details, evaluated subjects, and dynamic totals.",
    step5_cons_btn: "Download Excel (.xlsx)",
    step5_subj_title: "📑 Subject-Wise Sheets",
    step5_subj_desc: "Dedicated worksheet tab per subject with Theory, Practical & Sessional splits.",
    step5_subj_btn: "Download Subject Excel",
    step5_zip_title: "📂 Marksheets Archive",
    step5_zip_desc: "ZIP archive containing all downloaded student marksheet PDFs.",
    step5_zip_btn: "Download Marksheets (.zip)",
    step5_pkg_title: "📦 Complete Package",
    step5_pkg_desc: "Full bundle: Consolidated Excel, Subject Sheets, PDFs & Summary report.",
    step5_pkg_btn: "Download Full Package (.zip)",
    step5_retention_notice: "Files are retained for 30 minutes under our privacy lifecycle policy.",
    step5_reset_btn: "Start New Batch",

    // Consent Modal
    consent_title: "Transparent Processing Consent",
    consent_p1: "Before proceeding to server-side query execution, please review our privacy data handling notice:",
    consent_li1: "<strong>What leaves the browser:</strong> Only the student identifiers (Enrollment/Roll No and DOB) necessary to query the examination portal.",
    consent_li2: "<strong>Where requests go:</strong> Requests are dispatched directly to the official university result website matched above.",
    consent_li3: "<strong>Temporary Storage:</strong> Result PDFs and generated spreadsheets are stored on the server for a maximum of 30 minutes (TTL) and then purged automatically.",
    consent_li4: "<strong>Zero Tracking:</strong> No student names or marks are recorded in permanent databases or server activity logs.",
    consent_accept_btn: "I Understand & Proceed",
    consent_cancel_btn: "Cancel",

    // History Panel
    history_title: "Local Processing History",
    history_desc: "Stored only in your browser's local storage. Never sent to any server.",
    history_clear_all: "Clear All History",
    history_empty: "No local processing history recorded yet.",
    history_col_date: "Date & Time",
    history_col_portal: "Portal / University",
    history_col_records: "Records",
    history_col_status: "Status",
    history_col_actions: "Actions",

    // Offline Banner
    offline_msg: "⚠️ You are currently offline. University result queries require an active internet connection."
  },

  hi: {
    // Navigation
    nav_home: "होम",
    nav_how_it_works: "यह कैसे काम करता है",
    nav_universities: "समर्थित विश्वविद्यालय",
    nav_faq: "अक्सर पूछे जाने वाले प्रश्न",
    nav_contact: "संपर्क",
    nav_process: "रिजल्ट प्रोसेस करें",
    nav_history: "लोकल हिस्ट्री",

    // Hero
    hero_badge: "✓ 100% निःशुल्क और ओपन सोर्स • MIT लाइसेंस",
    hero_tagline: "थोक में शैक्षणिक परीक्षा परिणाम प्रोसेसिंग को सरल बनाएं।",
    hero_launch_btn: "🚀 परिणाम प्रोसेसिंग शुरू करें",
    hero_learn_btn: "कार्यप्रणाली समझें",

    // Step 1
    step1_title: "1. रिजल्ट पोर्टल का चयन करें",
    step1_desc: "कॉलेज या विश्वविद्यालय परीक्षा पोर्टल का URL दर्ज करें",
    step1_input_label: "रिजल्ट पोर्टल URL",
    step1_validate_btn: "पोर्टल सत्यापित करें",
    step1_quick_title: "त्वरित चयन:",
    step1_bteup_btn: "BTEUP आधिकारिक पोर्टल",
    step1_demo_btn: "मानक विश्वविद्यालय (डेमो और परीक्षण)",

    // Step 2
    step2_title: "2. छात्र सूची अपलोड करें (Excel)",
    step2_desc: "आपके ब्राउज़र में स्थानीय रूप से विश्लेषित",
    step2_drop_text: "अपनी छात्र Excel फ़ाइल यहाँ खींचें और छोड़ें, या चुनने के लिए क्लिक करें",
    step2_drop_hint: "छात्र नामांकन संख्या (Enrollment/Roll No) वाली .xlsx और .xls फ़ाइलें समर्थित हैं",
    step2_badge_local: "🔒 क्लाइंट-साइड लोकल पार्सिंग सक्रिय",
    step2_template_text: "क्या आपको एक्सेल फॉर्मेट टेम्पलेट चाहिए?",
    step2_template_btn: "⬇ एक्सेल नमूना टेम्पलेट डाउनलोड करें",
    step2_total_rows: "कुल पंक्तियाँ",
    step2_valid_rows: "मान्य रिकॉर्ड",
    step2_dup_rows: "डुप्लिकेट प्रविष्टियाँ",
    step2_empty_rows: "रिक्त पंक्तियाँ",
    step2_map_label: "एक्सेल कॉलम की पुष्टि या मैपिंग करें:",
    step2_map_enr: "नामांकन / रोल नंबर कॉलम *",
    step2_map_dob: "जन्म तिथि (DOB) कॉलम",
    step2_map_name: "छात्र का नाम कॉलम",
    step2_preview_title: "छात्र रिकॉर्ड पूर्वावलोकन (प्रथम 10 पंक्तियाँ):",

    // Step 3
    step3_title: "3. डेटा निष्कर्षण विकल्प चुनें",
    step3_desc: "आवश्यक फ़ील्ड और निर्यात प्रारूप चुनें",
    step3_opt_all: "सभी विषय (All Subjects)",
    step3_opt_theory: "थ्योरी अंक (Theory Marks)",
    step3_opt_practical: "प्रैक्टिकल अंक (Practical Marks)",
    step3_opt_internal: "आंतरिक / सेशनल अंक (Internal Marks)",
    step3_opt_subject_pct: "विषयवार प्रतिशत (Subject %)",
    step3_opt_totals: "कुल अंक (प्राप्तांक / पूर्णांक)",
    step3_opt_percentage: "समग्र प्रतिशत (Overall %)",
    step3_opt_status: "उत्तीर्ण / अनुत्तीर्ण स्थिति (Pass/Fail)",
    step3_opt_pdf: "व्यक्तिगत रिपोर्ट PDF",
    step3_opt_force: "पुनः डाउनलोड करें (कैश बायपास)",
    step3_start_btn: "▶ थोक परिणाम निष्कर्षण प्रारंभ करें",

    // Step 4
    step4_processing_title: "छात्र परिणाम निष्कर्षण जारी है",
    step4_cancel_btn: "⏹ प्रोसेसिंग रद्द करें",
    step4_total: "कुल",
    step4_success: "सफल",
    step4_failed: "विफल",
    step4_skipped: "छोड़े गए",
    step4_stream_title: "लाइव परिणाम तालिका:",
    step4_retry_failed_btn: "🔄 सभी विफल पुनः प्रयास करें",

    // Step 5
    step5_title: "5. परिणाम निर्यात एवं डाउनलोड करें",
    step5_desc: "डायनेमिक एक्सेल गणना एवं सुरक्षित मूल मार्कशीट",
    step5_cons_title: "📊 समेकित एक्सेल (Master Sheet)",
    step5_cons_desc: "छात्र विवरण, निकाले गए अंक और गतिशील योग के साथ मास्टर स्प्रेडशीट।",
    step5_cons_btn: "एक्सेल डाउनलोड (.xlsx)",
    step5_subj_title: "📑 विषयवार एक्सेल शीट्स",
    step5_subj_desc: "थ्योरी, प्रैक्टिकल और सेशनल विवरण के साथ प्रत्येक विषय के लिए अलग टैब।",
    step5_subj_btn: "विषयवार एक्सेल डाउनलोड",
    step5_zip_title: "📂 मार्कशीट संग्रह (ZIP)",
    step5_zip_desc: "सभी डाउनलोड किए गए छात्र मार्कशीट PDF की ज़िप फ़ाइल।",
    step5_zip_btn: "मार्कशीट डाउनलोड (.zip)",
    step5_pkg_title: "📦 संपूर्ण परिणाम पैकेज",
    step5_pkg_desc: "समेकित एक्सेल, विषयवार शीट्स, सभी PDF और सारांश रिपोर्ट का पूरा बंडल।",
    step5_pkg_btn: "पूरा पैकेज डाउनलोड (.zip)",
    step5_retention_notice: "हमारी गोपनीयता नीति के तहत फ़ाइलें 30 मिनट तक सर्वर पर सुरक्षित रहती हैं।",
    step5_reset_btn: "नया बैच शुरू करें",

    // Consent Modal
    consent_title: "पारदर्शी डेटा प्रोसेसिंग सहमति",
    consent_p1: "सर्वर-साइड निष्पादन शुरू करने से पहले, कृपया हमारी गोपनीयता सूचना पढ़ें:",
    consent_li1: "<strong>क्या ब्राउज़र छोड़ता है:</strong> केवल परीक्षा पोर्टल से परिणाम खोजने के लिए आवश्यक रोल नंबर और जन्म तिथि।",
    consent_li2: "<strong>अनुरोध कहाँ जाते हैं:</strong> संबंधित विश्वविद्यालय की आधिकारिक परीक्षा वेबसाइट पर सीधे भेजे जाते हैं।",
    consent_li3: "<strong>अस्थायी भंडारण:</strong> परिणाम PDF और स्प्रेडशीट अधिकतम 30 मिनट (TTL) के लिए रखे जाते हैं और स्वतः मिटा दिए जाते हैं।",
    consent_li4: "<strong>शून्य ट्रैकिंग:</strong> किसी भी स्थायी डेटाबेस में छात्र का नाम या अंक संग्रहीत नहीं किए जाते हैं।",
    consent_accept_btn: "मैं समझता हूँ और आगे बढ़ें",
    consent_cancel_btn: "रद्द करें",

    // History Panel
    history_title: "स्थानीय प्रोसेसिंग इतिहास (लोकल हिस्ट्री)",
    history_desc: "केवल आपके ब्राउज़र में सुरक्षित। कभी किसी सर्वर पर नहीं भेजा जाता।",
    history_clear_all: "सभी इतिहास साफ़ करें",
    history_empty: "अभी तक कोई स्थानीय प्रोसेसिंग इतिहास दर्ज नहीं हुआ है।",
    history_col_date: "दिनांक व समय",
    history_col_portal: "पोर्टल / विश्वविद्यालय",
    history_col_records: "रिकॉर्ड्स",
    history_col_status: "स्थिति",
    history_col_actions: "कार्रवाई",

    // Offline Banner
    offline_msg: "⚠️ आप वर्तमान में ऑफ़लाइन हैं। परिणाम खोजने के लिए सक्रिय इंटरनेट कनेक्शन आवश्यक है।"
  }
};
