// SkillSum ResultSetu - Frontend Controller
// Supports Bilingual Interface (EN/HI), PWA Offline Shell, Local History,
// Client-Side Excel Validation, and Transparent Processing Consent.

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  let currentLanguage = localStorage.getItem("app_lang") || "en";
  let currentConnectorId = "bteup";
  let currentJobId = null;
  let pollInterval = null;
  let clientParsedStudents = null;
  let serverUploadId = null;
  let brandConfig = {};

  // History storage key
  const HISTORY_STORAGE_KEY = "skillsum_resultsetu_history";

  // DOM Elements - Navigation & Views
  const navLinks = document.querySelectorAll(".nav-link[data-nav]");
  const allNavTriggers = document.querySelectorAll("[data-nav]");
  const pageViews = document.querySelectorAll(".page-view");
  const mobileNavToggle = document.getElementById("mobileNavToggle");
  const navLinksContainer = document.getElementById("navLinks");
  const offlineBanner = document.getElementById("offlineBanner");

  // Language Switcher Buttons
  const btnLangEn = document.getElementById("btnLangEn");
  const btnLangHi = document.getElementById("btnLangHi");

  // Process Workflow Elements
  const portalUrlInput = document.getElementById("portalUrl");
  const btnValidateUrl = document.getElementById("btnValidateUrl");
  const portalStatusBox = document.getElementById("portalStatusBox");
  const portalStatusIcon = document.getElementById("portalStatusIcon");
  const portalStatusText = document.getElementById("portalStatusText");

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const uploadAnalysisPanel = document.getElementById("uploadAnalysisPanel");

  const statTotalRows = document.getElementById("statTotalRows");
  const statValidRows = document.getElementById("statValidRows");
  const statDuplicateRows = document.getElementById("statDuplicateRows");
  const statEmptyRows = document.getElementById("statEmptyRows");

  const mapEnrollment = document.getElementById("mapEnrollment");
  const mapDob = document.getElementById("mapDob");
  const mapName = document.getElementById("mapName");

  const previewTableHead = document.getElementById("previewTableHead");
  const previewTableBody = document.getElementById("previewTableBody");
  const previewNotice = document.getElementById("previewNotice");

  const btnStartBulk = document.getElementById("btnStartBulk");
  const step4Card = document.getElementById("step4-card");
  const step5Card = document.getElementById("step5-card");

  const progressBar = document.getElementById("progressBar");
  const progressPercentage = document.getElementById("progressPercentage");
  const currentStatusBadge = document.getElementById("currentStatusBadge");
  const btnCancelProcess = document.getElementById("btnCancelProcess");

  const metricTotal = document.getElementById("metricTotal");
  const metricSuccess = document.getElementById("metricSuccess");
  const metricFailed = document.getElementById("metricFailed");
  const metricSkipped = document.getElementById("metricSkipped");

  const logTerminal = document.getElementById("logTerminal");
  const liveResultsBody = document.getElementById("liveResultsBody");
  const btnRetryFailed = document.getElementById("btnRetryFailed");

  // Export Download Links
  const btnDownloadConsolidated = document.getElementById("btnDownloadConsolidated");
  const btnDownloadSubjectWise = document.getElementById("btnDownloadSubjectWise");
  const btnDownloadMarksheetsZip = document.getElementById("btnDownloadMarksheetsZip");
  const btnDownloadCompleteZip = document.getElementById("btnDownloadCompleteZip");
  const btnResetApp = document.getElementById("btnResetApp");

  // Consent Modal Elements
  const consentModal = document.getElementById("consentModal");
  const btnConsentCancel = document.getElementById("btnConsentCancel");
  const btnConsentConfirm = document.getElementById("btnConsentConfirm");

  // History Elements
  const historyTableBody = document.getElementById("historyTableBody");
  const btnClearHistory = document.getElementById("btnClearHistory");

  // Column synonyms for client-side auto-detection
  const COLUMN_SYNONYMS = {
    enrollment: [
      "enrollment_number", "enrollment", "enrolment", "enrollmentno",
      "enrollment no", "enrolment no", "roll", "rollno", "roll no",
      "roll number", "registration", "reg no", "regno", "studentid",
      "student id", "enr", "enrno", "enr no", "enrollment_num", "roll_num", "seat_no"
    ],
    dob: [
      "date_of_birth", "dob", "date of birth", "birthdate", "birth date",
      "birth", "dateofbirth", "d_o_b"
    ],
    name: [
      "name", "student name", "student_name", "candidate name",
      "candidate_name", "student", "full_name"
    ]
  };

  function normalize(str) {
    return String(str || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  }

  // --- 1. Bilingual Localization (EN / HI) ---
  function setLanguage(lang) {
    currentLanguage = lang === "hi" ? "hi" : "en";
    localStorage.setItem("app_lang", currentLanguage);

    if (btnLangEn && btnLangHi) {
      if (currentLanguage === "hi") {
        btnLangHi.classList.add("active");
        btnLangEn.classList.remove("active");
      } else {
        btnLangEn.classList.add("active");
        btnLangHi.classList.remove("active");
      }
    }

    const dict = (typeof TRANSLATIONS !== "undefined" && TRANSLATIONS[currentLanguage])
      ? TRANSLATIONS[currentLanguage]
      : (typeof TRANSLATIONS !== "undefined" ? TRANSLATIONS.en : {});

    // Update all elements with data-i18n
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        el.innerHTML = dict[key];
      }
    });

    renderHistory();
  }

  if (btnLangEn) btnLangEn.addEventListener("click", () => setLanguage("en"));
  if (btnLangHi) btnLangHi.addEventListener("click", () => setLanguage("hi"));


  // --- 2. PWA Registration & Offline Detection ---
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/sw.js").catch(err => {
      console.warn("ServiceWorker registration notice:", err);
    });
  }

  function updateNetworkStatus() {
    if (offlineBanner) {
      offlineBanner.style.display = navigator.onLine ? "none" : "block";
    }
  }
  window.addEventListener("online", updateNetworkStatus);
  window.addEventListener("offline", updateNetworkStatus);
  updateNetworkStatus();


  // --- 3. Client-Side Page Router ---
  function navigateTo(targetViewId) {
    const validViews = [
      "home", "process", "history", "how-it-works", "universities",
      "guide", "about", "faq", "privacy", "terms", "disclaimer",
      "data-handling", "copyright", "contact", "license"
    ];

    const cleanTarget = validViews.includes(targetViewId) ? targetViewId : "home";

    pageViews.forEach(view => {
      if (view.id === `view-${cleanTarget}`) {
        view.classList.add("active");
      } else {
        view.classList.remove("active");
      }
    });

    navLinks.forEach(link => {
      if (link.getAttribute("data-nav") === cleanTarget) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    if (cleanTarget === "history") {
      renderHistory();
    }

    if (navLinksContainer) navLinksContainer.classList.remove("open");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  allNavTriggers.forEach(el => {
    el.addEventListener("click", e => {
      const target = el.getAttribute("data-nav");
      if (target) {
        e.preventDefault();
        window.location.hash = target;
        navigateTo(target);
      }
    });
  });

  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "");
    if (hash) navigateTo(hash);
  });

  if (mobileNavToggle) {
    mobileNavToggle.addEventListener("click", () => {
      navLinksContainer.classList.toggle("open");
    });
  }

  const initialHash = window.location.hash.replace("#", "") || "home";
  navigateTo(initialHash);

  // Dynamic Footer Year
  const footerYear = document.getElementById("footerYear");
  if (footerYear) {
    footerYear.textContent = new Date().getFullYear();
  }

  // FAQ Accordion Click Handler
  document.addEventListener("click", e => {
    const question = e.target.closest(".faq-question");
    if (question) {
      const item = question.closest(".faq-item");
      if (item) {
        item.classList.toggle("open");
      }
    }
  });


  // --- 4. Central Branding Configuration ---
  async function loadBrandingConfig() {
    try {
      const res = await fetch("/api/config");
      const data = await res.json();
      if (data.success && data.config) {
        brandConfig = data.config;
        document.querySelectorAll(".brand-text-name").forEach(el => {
          el.textContent = brandConfig.project_name || "SkillSum ResultSetu";
        });
        document.querySelectorAll(".brand-text-tagline").forEach(el => {
          el.textContent = brandConfig.tagline || "Simplify bulk academic result processing.";
        });
        document.querySelectorAll(".brand-text-support").forEach(el => {
          el.textContent = brandConfig.support_email || "[SUPPORT_EMAIL_PLACEHOLDER]";
        });
      }
    } catch (e) {
      console.warn("Using local configuration.");
    }
  }
  loadBrandingConfig();
  setLanguage(currentLanguage);


  // --- 5. Portal URL Validation ---
  validatePortalUrl(portalUrlInput.value);

  document.querySelectorAll(".btn-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      portalUrlInput.value = pill.getAttribute("data-url");
      validatePortalUrl(portalUrlInput.value);
    });
  });

  if (btnValidateUrl) {
    btnValidateUrl.addEventListener("click", () => {
      validatePortalUrl(portalUrlInput.value);
    });
  }

  async function validatePortalUrl(url) {
    if (!url || !url.trim()) return;
    try {
      const res = await fetch("/api/portals/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() })
      });
      const data = await res.json();

      portalStatusBox.style.display = "flex";
      if (data.supported) {
        currentConnectorId = data.connector_id;
        portalStatusBox.className = "portal-status-box matched";
        portalStatusIcon.textContent = "✓";
        const fieldsList = data.required_fields.map(f => f.label).join(", ");
        portalStatusText.innerHTML = `
          <strong>${data.portal_name}:</strong> ${data.description}<br/>
          <small>Required Student Fields: <strong>${fieldsList}</strong></small>
        `;
      } else {
        currentConnectorId = null;
        portalStatusBox.className = "portal-status-box unsupported";
        portalStatusIcon.textContent = "⚠";
        portalStatusText.innerHTML = `<strong>Unsupported Portal:</strong> ${data.message.replace(/\n/g, '<br/>')}`;
      }
    } catch (err) {
      console.error("Portal validation notice:", err);
    }
  }


  // --- 6. Privacy-First Client-Side Excel Parsing & Validation ---
  dropzone.addEventListener("click", () => fileInput.click());

  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", e => {
    const files = e.dataTransfer.files;
    if (files.length) processExcelFile(files[0]);
  });

  fileInput.addEventListener("change", e => {
    if (e.target.files.length) processExcelFile(e.target.files[0]);
  });

  async function processExcelFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!["xlsx", "xls"].includes(ext)) {
      alert("Please upload a valid Excel spreadsheet (.xlsx or .xls)");
      return;
    }

    dropzone.innerHTML = `<div class="upload-text">Reading & validating <strong>${file.name}</strong> locally...</div>`;

    if (window.XLSX) {
      try {
        const arrayBuffer = await file.arrayBuffer();
        const workbook = XLSX.read(arrayBuffer, { type: "array", cellDates: true });
        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];
        const rawJson = XLSX.utils.sheet_to_json(sheet, { defval: "" });

        if (!rawJson || rawJson.length === 0) {
          throw new Error("Excel spreadsheet contains no data rows.");
        }

        const columns = Object.keys(rawJson[0]);

        // Auto-detect columns
        const detected = { enrollment: null, dob: null, name: null };
        const normCols = {};
        columns.forEach(c => normCols[normalize(c)] = c);

        for (const [key, synList] of Object.entries(COLUMN_SYNONYMS)) {
          for (const syn of synList) {
            const nSyn = normalize(syn);
            if (normCols[nSyn]) {
              detected[key] = normCols[nSyn];
              break;
            }
          }
        }

        clientParsedStudents = {
          filename: file.name,
          columns: columns,
          detectedMapping: detected,
          rows: rawJson
        };
        serverUploadId = null;

        const enrollmentCol = detected.enrollment || columns[0];
        let emptyCount = 0;
        let dupCount = 0;
        const seen = new Set();

        rawJson.forEach(row => {
          const val = String(row[enrollmentCol] || "").trim();
          if (!val) {
            emptyCount++;
          } else if (seen.has(val)) {
            dupCount++;
          } else {
            seen.add(val);
          }
        });

        statTotalRows.textContent = rawJson.length;
        statValidRows.textContent = seen.size;
        statDuplicateRows.textContent = dupCount;
        statEmptyRows.textContent = emptyCount;

        populateColumnSelect(mapEnrollment, columns, detected.enrollment, true);
        populateColumnSelect(mapDob, columns, detected.dob, false);
        populateColumnSelect(mapName, columns, detected.name, false);

        renderPreviewTable(columns, rawJson.slice(0, 10));
        previewNotice.textContent = `Showing first ${Math.min(10, rawJson.length)} rows (100% browser-local verification)`;

        dropzone.innerHTML = `
          <div class="upload-icon" style="color: var(--success);">✓</div>
          <div class="upload-text"><strong>${file.name}</strong> loaded locally</div>
          <div class="upload-hint">Original file remains on your device &bull; Click to replace</div>
          <div><span class="privacy-badge-local">🔒 Client-Side Local Parsing Complete</span></div>
        `;

        uploadAnalysisPanel.style.display = "block";
        return;

      } catch (err) {
        console.warn("Client parsing fallback to server API:", err);
      }
    }

    // Fallback: Server-side upload API
    await uploadFileToServer(file);
  }

  async function uploadFileToServer(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });
      const resData = await res.json();

      if (!res.ok || !resData.success) {
        throw new Error(resData.detail || "Server upload failed");
      }

      const d = resData.data;
      serverUploadId = d.upload_id;
      clientParsedStudents = null;

      dropzone.innerHTML = `
        <div class="upload-icon" style="color: var(--success);">✓</div>
        <div class="upload-text"><strong>${d.filename}</strong> verified</div>
        <div class="upload-hint">Click or drop another file to replace</div>
      `;

      statTotalRows.textContent = d.total_rows;
      statValidRows.textContent = d.valid_count;
      statDuplicateRows.textContent = d.duplicate_count;
      statEmptyRows.textContent = d.empty_count;

      populateColumnSelect(mapEnrollment, d.columns, d.detected_mapping.enrollment, true);
      populateColumnSelect(mapDob, d.columns, d.detected_mapping.dob, false);
      populateColumnSelect(mapName, d.columns, d.detected_mapping.name, false);

      renderPreviewTable(d.columns, d.preview_records);
      previewNotice.textContent = `Showing first ${d.preview_records.length} sample rows`;

      uploadAnalysisPanel.style.display = "block";
    } catch (err) {
      alert("Error reading Excel spreadsheet: " + err.message);
      dropzone.innerHTML = `
        <div class="upload-icon">📄</div>
        <div class="upload-text">Drag & drop your Excel file here, or click to browse</div>
      `;
    }
  }

  function populateColumnSelect(selectElem, columns, preselectedValue, required) {
    selectElem.innerHTML = "";
    if (!required) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "-- Not in File / Optional --";
      selectElem.appendChild(opt);
    }
    columns.forEach(col => {
      const opt = document.createElement("option");
      opt.value = col;
      opt.textContent = col;
      if (preselectedValue && col.toLowerCase() === preselectedValue.toLowerCase()) {
        opt.selected = true;
      }
      selectElem.appendChild(opt);
    });
  }

  function renderPreviewTable(columns, rows) {
    previewTableHead.innerHTML = "";
    previewTableBody.innerHTML = "";

    columns.forEach(c => {
      const th = document.createElement("th");
      th.textContent = c;
      previewTableHead.appendChild(th);
    });

    rows.forEach(r => {
      const tr = document.createElement("tr");
      columns.forEach(c => {
        const td = document.createElement("td");
        let val = r[c];
        if (val instanceof Date) {
          val = val.toLocaleDateString("en-GB");
        }
        td.textContent = (val !== undefined && val !== null && val !== "") ? val : "-";
        tr.appendChild(td);
      });
      previewTableBody.appendChild(tr);
    });
  }


  // --- 7. Transparent Processing Consent & Start ---
  btnStartBulk.addEventListener("click", () => {
    if (!clientParsedStudents && !serverUploadId) {
      alert("Please upload a student Excel file in Step 2 before starting processing.");
      return;
    }

    if (!mapEnrollment.value) {
      alert("Please select the Enrollment Number / Roll Number column.");
      return;
    }

    const portalUrl = portalUrlInput.value.trim();
    if (!portalUrl) {
      alert("Please provide a valid Result Portal URL in Step 1.");
      return;
    }

    // Open Transparent Consent Modal before initiating queries
    consentModal.style.display = "flex";
  });

  btnConsentCancel.addEventListener("click", () => {
    consentModal.style.display = "none";
  });

  btnConsentConfirm.addEventListener("click", () => {
    consentModal.style.display = "none";
    executeBulkProcessing();
  });

  async function executeBulkProcessing() {
    const portalUrl = portalUrlInput.value.trim();

    const options = {
      include_all_subjects: document.getElementById("optAllSubjects").checked,
      include_theory: document.getElementById("optTheory").checked,
      include_practical: document.getElementById("optPractical").checked,
      include_internal: document.getElementById("optInternal").checked,
      include_subject_pct: document.getElementById("optSubjectPct").checked,
      include_totals: document.getElementById("optTotals").checked,
      include_percentage: document.getElementById("optPercentage").checked,
      include_status: document.getElementById("optStatus").checked,
      download_pdf: document.getElementById("optPdf").checked,
      force_download: document.getElementById("optForceDownload").checked,
    };

    btnStartBulk.disabled = true;
    btnStartBulk.textContent = "Starting Bulk Processing...";

    try {
      let res, data;

      if (clientParsedStudents) {
        const enrCol = mapEnrollment.value;
        const dobCol = mapDob.value;
        const nameCol = mapName.value;

        const studentPayload = [];
        const seenEnr = new Set();

        clientParsedStudents.rows.forEach(r => {
          let enrVal = String(r[enrCol] || "").trim();
          if (enrVal.endsWith(".0")) enrVal = enrVal.slice(0, -2);

          if (!enrVal || seenEnr.has(enrVal)) return;
          seenEnr.add(enrVal);

          let dobVal = "";
          if (dobCol && r[dobCol]) {
            const raw = r[dobCol];
            if (raw instanceof Date) {
              const d = String(raw.getDate()).padStart(2, '0');
              const m = String(raw.getMonth() + 1).padStart(2, '0');
              const y = raw.getFullYear();
              dobVal = `${d}/${m}/${y}`;
            } else {
              dobVal = String(raw).trim();
            }
          }

          let nameVal = nameCol && r[nameCol] ? String(r[nameCol]).trim() : "";

          studentPayload.push({
            enrollment: enrVal,
            dob: dobVal,
            name: nameVal
          });
        });

        res = await fetch("/api/process/start_direct", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            portal_url: portalUrl,
            connector_id: currentConnectorId || "bteup",
            students: studentPayload,
            options: options
          })
        });

      } else {
        res = await fetch("/api/process/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            upload_id: serverUploadId,
            portal_url: portalUrl,
            connector_id: currentConnectorId || "bteup",
            column_mapping: {
              enrollment: mapEnrollment.value,
              dob: mapDob.value,
              name: mapName.value
            },
            options: options
          })
        });
      }

      data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.detail || "Unable to initiate processing session.");
      }

      currentJobId = data.job_id;

      step4Card.style.display = "block";
      step4Card.scrollIntoView({ behavior: "smooth" });

      startStatusPolling(currentJobId, portalUrl);

    } catch (err) {
      alert("Processing error: " + err.message);
      btnStartBulk.disabled = false;
      btnStartBulk.textContent = "▶ Start Bulk Processing";
    }
  }


  // --- 8. Cancellation Support ---
  if (btnCancelProcess) {
    btnCancelProcess.addEventListener("click", async () => {
      if (!currentJobId) return;
      if (confirm("Are you sure you want to cancel the active processing session?")) {
        btnCancelProcess.disabled = true;
        btnCancelProcess.textContent = "Cancelling...";
        try {
          await fetch(`/api/process/cancel/${currentJobId}`, { method: "POST" });
        } catch (e) {
          console.error("Cancellation notice:", e);
        }
      }
    });
  }


  // --- 9. Live Polling & Real-Time Stream ---
  function startStatusPolling(jobId, portalUrl) {
    if (pollInterval) clearInterval(pollInterval);
    if (btnCancelProcess) {
      btnCancelProcess.disabled = false;
      btnCancelProcess.textContent = "⏹ Cancel Processing";
    }

    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/process/status/${jobId}`);
        if (!res.ok) return;

        const data = await res.json();
        const job = data.job;

        progressBar.style.width = `${job.percent}%`;
        progressPercentage.textContent = `${job.percent}%`;
        currentStatusBadge.textContent = job.status.toUpperCase();

        if (job.status === "completed") {
          currentStatusBadge.className = "badge badge-success";
        } else if (job.status === "failed" || job.status === "cancelled") {
          currentStatusBadge.className = "badge badge-fail";
        } else {
          currentStatusBadge.className = "badge badge-info";
        }

        metricTotal.textContent = job.total;
        metricSuccess.textContent = job.successful;
        metricFailed.textContent = job.failed;
        metricSkipped.textContent = job.skipped;

        logTerminal.innerHTML = "";
        job.recent_logs.forEach(msg => {
          const d = document.createElement("div");
          d.textContent = msg;
          logTerminal.appendChild(d);
        });
        logTerminal.scrollTop = logTerminal.scrollHeight;

        renderLiveResults(job.results);

        if (job.failed > 0 && job.status === "completed") {
          btnRetryFailed.style.display = "inline-flex";
        } else {
          btnRetryFailed.style.display = "none";
        }

        if (job.status === "completed" || job.status === "failed" || job.status === "cancelled") {
          clearInterval(pollInterval);
          btnStartBulk.disabled = false;
          btnStartBulk.textContent = "▶ Start Bulk Processing";

          // Save batch metadata to Local History
          recordLocalHistory({
            job_id: jobId,
            timestamp: new Date().toLocaleString(),
            portal_url: portalUrl || job.portal_url,
            total: job.total,
            successful: job.successful,
            failed: job.failed,
            skipped: job.skipped,
            status: job.status
          });

          setupExportLinks(jobId);
          step5Card.style.display = "block";
        }

      } catch (e) {
        console.error("Polling notice:", e);
      }
    }, 1000);
  }

  function renderLiveResults(results) {
    liveResultsBody.innerHTML = "";
    results.forEach((r, idx) => {
      const tr = document.createElement("tr");

      let statusBadge = `<span class="badge badge-gray">${r.status}</span>`;
      if (r.status === "Success" || r.status === "Cached") {
        statusBadge = `<span class="badge badge-success">${r.status}</span>`;
      } else if (r.status === "Failed") {
        statusBadge = `<span class="badge badge-fail" title="${r.error_message}">Failed</span>`;
      } else if (r.status === "Skipped") {
        statusBadge = `<span class="badge badge-warn" title="${r.error_message}">Skipped</span>`;
      }

      // Verification warning indicator
      let verifyBadge = "";
      if (r.verification_flags && r.verification_flags.length > 0) {
        verifyBadge = ` <span class="badge badge-warn" title="${r.verification_flags.join('; ')}">⚠️ Review</span>`;
      }

      let pdfCell = "-";
      if (r.pdf_path) {
        pdfCell = `<a href="/api/download/${currentJobId}/pdf?enrollment=${encodeURIComponent(r.enrollment)}" target="_blank" class="btn btn-secondary btn-sm">View PDF</a>`;
      }

      let actionCell = "-";
      if (r.status === "Failed") {
        actionCell = `<button class="btn btn-secondary btn-sm btn-retry-single" data-enrollment="${r.enrollment}">🔄 Retry</button>`;
      }

      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td><strong>${r.enrollment}</strong></td>
        <td>${r.student_name || "-"}</td>
        <td>${r.total_obtained ? `${r.total_obtained} / ${r.total_max}` : "-"}${verifyBadge}</td>
        <td>${r.overall_percentage ? `${r.overall_percentage}%` : "-"}</td>
        <td>${r.result_status || "-"}</td>
        <td>${statusBadge}</td>
        <td>${pdfCell}</td>
        <td>${actionCell}</td>
      `;
      liveResultsBody.appendChild(tr);
    });

    document.querySelectorAll(".btn-retry-single").forEach(btn => {
      btn.addEventListener("click", async () => {
        const enr = btn.getAttribute("data-enrollment");
        btn.disabled = true;
        btn.textContent = "Retrying...";
        try {
          await fetch(`/api/process/retry/${currentJobId}/${encodeURIComponent(enr)}`, { method: "POST" });
          startStatusPolling(currentJobId);
        } catch (e) {
          alert("Retry launch failed: " + e.message);
        }
      });
    });
  }

  btnRetryFailed.addEventListener("click", async () => {
    btnRetryFailed.disabled = true;
    btnRetryFailed.textContent = "Retrying all...";
    try {
      await fetch(`/api/process/retry-failed/${currentJobId}`, { method: "POST" });
      startStatusPolling(currentJobId);
    } catch (e) {
      alert("Bulk retry failed: " + e.message);
    } finally {
      btnRetryFailed.disabled = false;
    }
  });

  function setupExportLinks(jobId) {
    btnDownloadConsolidated.href = `/api/download/${jobId}/consolidated_excel`;
    btnDownloadSubjectWise.href = `/api/download/${jobId}/subject_excel`;
    btnDownloadMarksheetsZip.href = `/api/download/${jobId}/marksheets_zip`;
    btnDownloadCompleteZip.href = `/api/download/${jobId}/complete_zip`;
  }

  btnResetApp.addEventListener("click", async () => {
    if (confirm("Reset current batch and clear session files?")) {
      if (currentJobId) {
        try {
          await fetch(`/api/cleanup/${currentJobId}`, { method: "DELETE" });
        } catch (e) {}
      }
      window.location.reload();
    }
  });


  // --- 10. Local-Only Processing History Management ---
  function getLocalHistory() {
    try {
      const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      return [];
    }
  }

  function recordLocalHistory(entry) {
    const history = getLocalHistory();
    // Prepend new entry
    history.unshift(entry);
    // Keep max 25 recent batch metadata entries
    if (history.length > 25) history.length = 25;
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
    renderHistory();
  }

  function renderHistory() {
    if (!historyTableBody) return;
    const history = getLocalHistory();

    if (history.length === 0) {
      const emptyMsg = (typeof TRANSLATIONS !== "undefined" && TRANSLATIONS[currentLanguage] && TRANSLATIONS[currentLanguage].history_empty)
        ? TRANSLATIONS[currentLanguage].history_empty
        : "No local processing history recorded yet.";
      historyTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">${emptyMsg}</td></tr>`;
      return;
    }

    historyTableBody.innerHTML = "";
    history.forEach((h, idx) => {
      const tr = document.createElement("tr");

      let stClass = "badge-gray";
      if (h.status === "completed") stClass = "badge-success";
      else if (h.status === "failed") stClass = "badge-fail";

      const portalDisplay = h.portal_url ? h.portal_url.replace(/^https?:\/\//, '').split('/')[0] : "University Portal";

      tr.innerHTML = `
        <td>${h.timestamp}</td>
        <td><code>${portalDisplay}</code></td>
        <td>${h.total} records (${h.successful} success, ${h.failed} fail)</td>
        <td><span class="badge ${stClass}">${h.status}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm btn-del-history" data-index="${idx}" style="color: #991b1b;">Delete</button>
        </td>
      `;
      historyTableBody.appendChild(tr);
    });

    document.querySelectorAll(".btn-del-history").forEach(btn => {
      btn.addEventListener("click", () => {
        const itemIdx = parseInt(btn.getAttribute("data-index"), 10);
        deleteHistoryItem(itemIdx);
      });
    });
  }

  function deleteHistoryItem(idx) {
    const history = getLocalHistory();
    history.splice(idx, 1);
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
    renderHistory();
  }

  if (btnClearHistory) {
    btnClearHistory.addEventListener("click", () => {
      if (confirm("Permanently clear all local processing history from this browser?")) {
        localStorage.removeItem(HISTORY_STORAGE_KEY);
        renderHistory();
      }
    });
  }

  // --- 11. FAQ Accordions ---
  document.querySelectorAll(".faq-question").forEach(q => {
    q.addEventListener("click", () => {
      const item = q.parentElement;
      item.classList.toggle("open");
    });
  });

});
