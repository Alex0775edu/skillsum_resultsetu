// SkillSum ResultSetu - Bilingual Translation Dictionary (English + Hindi)
// Company: SkillSum Innovations | Founder: Aditya Rajak

const TRANSLATIONS = {
  en: {
    // Navigation
    nav_home: "Home",
    nav_process: "Process Results",
    nav_universities: "Supported Universities",
    nav_guide: "User Guide",
    nav_about: "About",
    nav_faq: "FAQ",
    nav_history: "Local History",
    nav_contact: "Contact",

    // Brand & Identity
    brand_presents: "SkillSum Innovations presents",
    brand_product: "SkillSum ResultSetu",
    brand_developed_by: "Developed by SkillSum Innovations",
    brand_founder: "Founded by Aditya Rajak",

    // Hero
    hero_badge: "✓ 100% Free & Open Source • MIT License",
    hero_tagline: "Simplify bulk academic result processing.",
    hero_launch_btn: "🚀 Launch Bulk Processing",
    hero_guide_btn: "📖 Read User Guide",
    hero_learn_btn: "Learn How It Works",

    // Self-Promotional Section (SkillSum Innovations)
    promo_badge: "SkillSum Innovations",
    promo_heading: "Need Technology Solutions for Your Business?",
    promo_subtext: "SkillSum Innovations helps businesses turn ideas into practical digital solutions.",
    promo_cta: "Explore SkillSum Services ↗",
    promo_s1_title: "Website Development",
    promo_s1_desc: "Custom modern websites, responsive web apps, and CMS portals built for performance.",
    promo_s2_title: "Software & Management Systems",
    promo_s2_desc: "Enterprise management, billing systems, and custom automation software.",
    promo_s3_title: "Embedded Systems & IoT",
    promo_s3_desc: "Smart hardware, microcontroller programming, and cloud-connected IoT devices.",
    promo_s4_title: "Video Editing & Production",
    promo_s4_desc: "Professional video editing, corporate presentations, and educational media.",
    promo_s5_title: "SEO & Digital Marketing",
    promo_s5_desc: "Targeted search engine optimization, content strategy, and online brand visibility.",
    promo_s6_title: "AI Solutions & Maintenance",
    promo_s6_desc: "AI workflow integration, smart data utilities, and dedicated software maintenance.",
    promo_footer_banner: "Need custom web, software or IoT systems for your organization? Partner with <strong>SkillSum Innovations</strong>.",

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
    step5_cons_desc: "Master sheet with student details, evaluated subjects, topper rankings, and class stats.",
    step5_cons_btn: "Download Excel (.xlsx)",
    step5_subj_title: "📑 Subject-Wise Sheets",
    step5_subj_desc: "Dedicated worksheet tab per subject with Theory, Practical & Sessional splits.",
    step5_subj_btn: "Download Subject Excel",
    step5_zip_title: "📂 Marksheets Archive",
    step5_zip_desc: "ZIP archive containing all downloaded student provisional marksheet PDFs.",
    step5_zip_btn: "Download Marksheets (.zip)",
    step5_pkg_title: "📦 Complete Package",
    step5_pkg_desc: "Full bundle: Consolidated Excel, Subject Sheets, PDFs & Summary report.",
    step5_pkg_btn: "Download Full Package (.zip)",
    step5_retention_notice: "Files are retained for 30 minutes under our privacy lifecycle policy.",
    step5_reset_btn: "Start New Batch",

    // User Guide
    guide_title: "Comprehensive User Guide",
    guide_subtitle: "Step-by-step instructions for students, educators, and college administrators",
    guide_start_btn: "🚀 Launch Bulk Processing Now",
    guide_step1_title: "Step 1: Prepare Your Excel File",
    guide_step2_title: "Step 2: Upload & Review Student List",
    guide_step3_title: "Step 3: Enter University Result Portal URL",
    guide_step4_title: "Step 4: Review Privacy Notice & Confirm",
    guide_step5_title: "Step 5: Monitor Live Bulk Processing",
    guide_step6_title: "Step 6: Verify Extracted Marks & Integrity",
    guide_step7_title: "Step 7: Download Reports & Packages",
    guide_step8_title: "Step 8: Manage Local Browser History",

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
    nav_process: "परिणाम प्रसंस्करण",
    nav_universities: "समर्थित विश्वविद्यालय",
    nav_guide: "उपयोगकर्ता गाइड",
    nav_about: "हमारे बारे में",
    nav_faq: "अक्सर पूछे जाने वाले प्रश्न",
    nav_history: "लोकल इतिहास",
    nav_contact: "संपर्क",

    // Brand & Identity
    brand_presents: "स्किलसम इनोवेशंस प्रस्तुत करता है",
    brand_product: "स्किलसम परिणामसेतु",
    brand_developed_by: "स्किलसम इनोवेशंस द्वारा विकसित",
    brand_founder: "संस्थापक: आदित्य रजक",

    // Hero
    hero_badge: "✓ 100% निःशुल्क एवं ओपन-सोर्स • MIT लाइसेंस",
    hero_tagline: "थोक शैक्षणिक परिणाम प्रसंस्करण को सरल बनाएं।",
    hero_launch_btn: "🚀 बल्क प्रोसेसिंग शुरू करें",
    hero_guide_btn: "📖 गाइड पढ़ें",
    hero_learn_btn: "यह कैसे काम करता है",

    // Self-Promotional Section (SkillSum Innovations)
    promo_badge: "स्किलसम इनोवेशंस",
    promo_heading: "क्या आपके व्यवसाय को तकनीकी समाधान चाहिए?",
    promo_subtext: "स्किलसम इनोवेशंस व्यवसायों के विचारों को व्यावहारिक डिजिटल समाधानों में बदलने में मदद करता है।",
    promo_cta: "स्किलसम सेवाओं को जानें ↗",
    promo_s1_title: "वेबसाइट विकास (वेब डेवलपमेंट)",
    promo_s1_desc: "आधुनिक कस्टम वेबसाइटें, रिस्पॉन्सिव वेब ऐप्स और बेहतरीन प्रदर्शन वाले CMS पोर्टल।",
    promo_s2_title: "सॉफ्टवेयर एवं प्रबंधन प्रणाली",
    promo_s2_desc: "एंटरप्राइज मैनेजमेंट सिस्टम, बिलिंग सॉफ्टवेयर और कस्टम ऑटोमेशन टूल्स।",
    promo_s3_title: "एम्बेडेड सिस्टम एवं IoT",
    promo_s3_desc: "स्मार्ट हार्डवेयर, माइक्रोकंट्रोलर प्रोग्रामिंग और क्लाउड-कनेक्टेड IoT डिवाइस।",
    promo_s4_title: "वीडियो एडिटिंग एवं प्रोडक्शन",
    promo_s4_desc: "पेशेवर वीडियो एडिटिंग, कॉर्पोरेट प्रस्तुतियाँ और शैक्षणिक मीडिया निर्माण।",
    promo_s5_title: "SEO एवं डिजिटल मार्केटिंग",
    promo_s5_desc: "सर्च इंजन अनुकूलन (SEO), कंटेंट रणनीति और ऑनलाइन ब्रांड दृश्यता।",
    promo_s6_title: "AI समाधान एवं रखरखाव",
    promo_s6_desc: "AI वर्कफ़्लो एकीकरण, डेटा उपकरण और समर्पित सॉफ्टवेयर रखरखाव।",
    promo_footer_banner: "क्या आपके संस्थान को कस्टम वेब, सॉफ्टवेयर या IoT समाधान चाहिए? <strong>स्किलसम इनोवेशंस</strong> के साथ साझेदारी करें।",

    // Step 1
    step1_title: "रिजल्ट पोर्टल चुनें",
    step1_desc: "कॉलेज या विश्वविद्यालय परीक्षा परिणाम पोर्टल का URL दर्ज करें",
    step1_input_label: "रिजल्ट पोर्टल URL",
    step1_validate_btn: "पोर्टल जांचें",
    step1_quick_title: "त्वरित चयन:",
    step1_bteup_btn: "BTEUP आधिकारिक पोर्टल",
    step1_demo_btn: "मानक विश्वविद्यालय (डेमो और परीक्षण)",

    // Step 2
    step2_title: "छात्र सूची अपलोड करें (Excel)",
    step2_desc: "आपके ब्राउज़र में स्थानीय रूप से संसाधित",
    step2_drop_text: "अपनी छात्र एक्सेल फ़ाइल यहाँ खींचें और छोड़ें, या चुनने के लिए क्लिक करें",
    step2_drop_hint: ".xlsx और .xls फ़ाइलों का समर्थन करता है",
    step2_badge_local: "🔒 क्लाइंट-साइड लोकल पार्सिंग सक्षम",
    step2_template_text: "संरचित प्रारूप टेम्पलेट चाहिए?",
    step2_template_btn: "⬇ सैंपल एक्सेल टेम्पलेट डाउनलोड करें",
    step2_total_rows: "कुल पंक्तियाँ",
    step2_valid_rows: "मान्य रिकॉर्ड",
    step2_dup_rows: "डुप्लिकेट पंक्तियाँ",
    step2_empty_rows: "खाली पंक्तियाँ",
    step2_map_label: "एक्सेल कॉलम की पुष्टि करें:",
    step2_map_enr: "नामांकन / रोल नंबर कॉलम *",
    step2_map_dob: "जन्म तिथि (DOB) कॉलम",
    step2_map_name: "छात्र का नाम कॉलम",
    step2_preview_title: "छात्र रिकॉर्ड पूर्वावलोकन (पहली 10 पंक्तियाँ):",

    // Step 3
    step3_title: "निष्कर्षण विकल्प कॉन्फ़िगर करें",
    step3_desc: "वांछित डेटा फ़ील्ड और निर्यात फ़ाइलें चुनें",
    step3_opt_all: "सभी विषय",
    step3_opt_theory: "थ्योरी अंक",
    step3_opt_practical: "प्रैक्टिकल अंक",
    step3_opt_internal: "आंतरिक / सेशनल अंक",
    step3_opt_subject_pct: "विषय-वार प्रतिशत",
    step3_opt_totals: "कुल अंक (प्राप्त / अधिकतम)",
    step3_opt_percentage: "कुल प्रतिशत (%)",
    step3_opt_status: "पास / फेल स्थिति",
    step3_opt_pdf: "व्यक्तिगत प्रदर्शन रिपोर्ट PDF",
    step3_opt_force: "पुनः डाउनलोड करें (कैश बायपास)",
    step3_start_btn: "▶ बल्क प्रोसेसिंग शुरू करें",

    // Step 4
    step4_processing_title: "छात्रों का परिणाम संसाधित हो रहा है",
    step4_cancel_btn: "⏹ प्रोसेसिंग रद्द करें",
    step4_total: "कुल",
    step4_success: "सफल",
    step4_failed: "असफल",
    step4_skipped: "छोड़े गए",
    step4_stream_title: "लाइव परिणाम स्ट्रीम:",
    step4_retry_failed_btn: "🔄 सभी असफल को पुनः प्रयास करें",

    // Step 5
    step5_title: "परिणाम निर्यात और डाउनलोड करें",
    step5_desc: "सटीक गणना और मूल मार्कशीट डेटा",
    step5_cons_title: "📊 समेकित एक्सेल",
    step5_cons_desc: "छात्र विवरण, मूल्यांकित विषय, टॉपर रैंकिंग और कक्षा आंकड़ों वाली मास्टर शीट।",
    step5_cons_btn: "एक्सेल डाउनलोड करें (.xlsx)",
    step5_subj_title: "📑 विषय-वार शीट्स",
    step5_subj_desc: "थ्योरी, प्रैक्टिकल और सेशनल विभाजन के साथ प्रत्येक विषय के लिए समर्पित टैब।",
    step5_subj_btn: "विषय-वार एक्सेल डाउनलोड करें",
    step5_zip_title: "📂 मार्कशीट संग्रह",
    step5_zip_desc: "सभी डाउनलोड की गई छात्र प्रोविजनल PDF मार्कशीट्स वाली ZIP फ़ाइल।",
    step5_zip_btn: "मार्कशीट डाउनलोड करें (.zip)",
    step5_pkg_title: "📦 संपूर्ण पैकेज",
    step5_pkg_desc: "पूरा बंडल: समेकित एक्सेल, विषय शीट्स, PDF और सारांश रिपोर्ट।",
    step5_pkg_btn: "पूरा पैकेज डाउनलोड करें (.zip)",
    step5_retention_notice: "फ़ाइलें हमारी गोपनीयता नीति के तहत 30 मिनट के लिए सुरक्षित रखी जाती हैं।",
    step5_reset_btn: "नया बैच शुरू करें",

    // User Guide
    guide_title: "विस्तृत उपयोगकर्ता मार्गदर्शिका",
    guide_subtitle: "छात्रों, शिक्षकों और कॉलेज प्रशासकों के लिए चरण-दर-चरण निर्देश",
    guide_start_btn: "🚀 परिणाम प्रसंस्करण शुरू करें",
    guide_step1_title: "चरण 1: अपनी एक्सेल फ़ाइल तैयार करें",
    guide_step2_title: "चरण 2: छात्र सूची अपलोड और पूर्वावलोकन करें",
    guide_step3_title: "चरण 3: विश्वविद्यालय परिणाम पोर्टल URL दर्ज करें",
    guide_step4_title: "चरण 4: गोपनीयता नोटिस की समीक्षा करें और पुष्टि करें",
    guide_step5_title: "चरण 5: लाइव बल्क प्रोसेसिंग देखें",
    guide_step6_title: "चरण 6: निकाले गए अंकों और डेटा की पुष्टि करें",
    guide_step7_title: "चरण 7: रिपोर्ट और पैकेज डाउनलोड करें",
    guide_step8_title: "चरण 8: स्थानीय ब्राउज़र इतिहास प्रबंधित करें",

    // Consent Modal
    consent_title: "पारदर्शी प्रसंस्करण सहमति",
    consent_p1: "सर्वर-साइड निष्पादन शुरू करने से पहले, कृपया हमारे गोपनीयता डेटा प्रबंधन नोटिस की समीक्षा करें:",
    consent_li1: "<strong>ब्राउज़र से क्या बाहर जाता है:</strong> केवल परीक्षा पोर्टल से परिणाम निकालने के लिए आवश्यक छात्र पहचानकर्ता (नामांकन/रोल नंबर और जन्मतिथि)।",
    consent_li2: "<strong>अनुरोध कहाँ जाते हैं:</strong> अनुरोध सीधे ऊपर चुने गए आधिकारिक विश्वविद्यालय परिणाम वेबसाइट पर भेजे जाते हैं।",
    consent_li3: "<strong>अस्थायी भंडारण:</strong> परिणाम PDF और एक्सेल स्प्रेडशीट सर्वर पर अधिकतम 30 मिनट तक संग्रहीत रहते हैं और फिर स्वतः हटा दिए जाते हैं।",
    consent_li4: "<strong>शून्य ट्रैकिंग:</strong> किसी भी स्थायी डेटाबेस या सर्वर लॉग में छात्रों के नाम या अंक कभी भी सहेजे नहीं जाते हैं।",
    consent_accept_btn: "मैं समझता हूँ और आगे बढ़ें",
    consent_cancel_btn: "रद्द करें",

    // History Panel
    history_title: "लोकल प्रोसेसिंग इतिहास",
    history_desc: "केवल आपके ब्राउज़र के लोकल स्टोरेज में संग्रहीत। किसी सर्वर पर कभी नहीं भेजा जाता।",
    history_clear_all: "सभी इतिहास साफ़ करें",
    history_empty: "अभी तक कोई लोकल प्रोसेसिंग इतिहास दर्ज नहीं है।",
    history_col_date: "दिनांक एवं समय",
    history_col_portal: "पोर्टल / विश्वविद्यालय",
    history_col_records: "रिकॉर्ड्स",
    history_col_status: "स्थिति",
    history_col_actions: "कार्रवाई",

    // Offline Banner
    offline_msg: "⚠️ आप वर्तमान में ऑफ़लाइन हैं। विश्वविद्यालय परिणाम प्रश्नों के लिए इंटरनेट कनेक्शन आवश्यक है।"
  }
};
