// Frontend Application Logic for Universal Bulk Result Processor

document.addEventListener("DOMContentLoaded", () => {
  // State variables
  let currentConnectorId = "bteup";
  let currentUploadId = null;
  let currentJobId = null;
  let pollInterval = null;
  let detectedMapping = {};
  let uploadedColumns = [];

  // DOM Elements
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

  const metricTotal = document.getElementById("metricTotal");
  const metricSuccess = document.getElementById("metricSuccess");
  const metricFailed = document.getElementById("metricFailed");
  const metricSkipped = document.getElementById("metricSkipped");

  const logTerminal = document.getElementById("logTerminal");
  const liveResultsBody = document.getElementById("liveResultsBody");
  const btnRetryFailed = document.getElementById("btnRetryFailed");

  // Export Links
  const btnDownloadConsolidated = document.getElementById("btnDownloadConsolidated");
  const btnDownloadSubjectWise = document.getElementById("btnDownloadSubjectWise");
  const btnDownloadMarksheetsZip = document.getElementById("btnDownloadMarksheetsZip");
  const btnDownloadCompleteZip = document.getElementById("btnDownloadCompleteZip");
  const btnResetApp = document.getElementById("btnResetApp");

  // 1. Initial URL validation on page load
  validatePortalUrl(portalUrlInput.value);

  // Quick select pills
  document.querySelectorAll(".btn-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      portalUrlInput.value = pill.getAttribute("data-url");
      validatePortalUrl(portalUrlInput.value);
    });
  });

  btnValidateUrl.addEventListener("click", () => {
    validatePortalUrl(portalUrlInput.value);
  });

  async function validatePortalUrl(url) {
    if (!url.trim()) return;
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
      console.error("Portal validation error:", err);
    }
  }

  // 2. Drag & Drop / File Upload
  dropzone.addEventListener("click", () => fileInput.click());

  ["dragenter", "dragover"].forEach(eventName => {
    dropzone.addEventListener(eventName, e => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropzone.addEventListener(eventName, e => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", e => {
    const files = e.dataTransfer.files;
    if (files.length) handleFileUpload(files[0]);
  });

  fileInput.addEventListener("change", e => {
    if (e.target.files.length) handleFileUpload(e.target.files[0]);
  });

  async function handleFileUpload(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!["xlsx", "xls"].includes(ext)) {
      alert("Please upload a valid Excel file (.xlsx or .xls)");
      return;
    }

    dropzone.innerHTML = `<div class="upload-text">Uploading & analyzing <strong>${file.name}</strong>...</div>`;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });
      const resData = await res.json();

      if (!res.ok || !resData.success) {
        throw new Error(resData.detail || "Upload failed");
      }

      const d = resData.data;
      currentUploadId = d.upload_id;
      uploadedColumns = d.columns;
      detectedMapping = d.detected_mapping;

      // Update dropzone UI
      dropzone.innerHTML = `
        <div class="upload-icon" style="color: var(--success);">✓</div>
        <div class="upload-text"><strong>${d.filename}</strong> uploaded successfully</div>
        <div class="upload-hint">Click or drop another file to replace</div>
      `;

      // Show stats
      statTotalRows.textContent = d.total_rows;
      statValidRows.textContent = d.valid_count;
      statDuplicateRows.textContent = d.duplicate_count;
      statEmptyRows.textContent = d.empty_count;

      // Populate column selectors
      populateColumnSelect(mapEnrollment, d.columns, detectedMapping.enrollment, true);
      populateColumnSelect(mapDob, d.columns, detectedMapping.dob, false);
      populateColumnSelect(mapName, d.columns, detectedMapping.name, false);

      // Render Preview Table
      renderPreviewTable(d.columns, d.preview_records);
      previewNotice.textContent = `Showing ${d.preview_records.length} sample rows`;

      uploadAnalysisPanel.style.display = "block";
    } catch (err) {
      alert("Error parsing Excel file: " + err.message);
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
      opt.textContent = "-- Not in Excel / Optional --";
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

    // Headers
    columns.forEach(c => {
      const th = document.createElement("th");
      th.textContent = c;
      previewTableHead.appendChild(th);
    });

    // Rows
    rows.forEach(r => {
      const tr = document.createElement("tr");
      columns.forEach(c => {
        const td = document.createElement("td");
        td.textContent = r[c] || "-";
        tr.appendChild(td);
      });
      previewTableBody.appendChild(tr);
    });
  }

  // 3. Start Bulk Processing
  btnStartBulk.addEventListener("click", async () => {
    if (!currentUploadId) {
      alert("Please upload an Excel file in Step 2 before starting processing.");
      return;
    }

    if (!mapEnrollment.value) {
      alert("Please map the Enrollment / Roll Number column.");
      return;
    }

    const portalUrl = portalUrlInput.value.trim();
    if (!portalUrl) {
      alert("Please enter a Result Portal URL in Step 1.");
      return;
    }

    // Extraction Options
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

    const columnMapping = {
      enrollment: mapEnrollment.value,
      dob: mapDob.value,
      name: mapName.value,
    };

    btnStartBulk.disabled = true;
    btnStartBulk.textContent = "Initiating Bulk Processing...";

    try {
      const res = await fetch("/api/process/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          upload_id: currentUploadId,
          portal_url: portalUrl,
          connector_id: currentConnectorId || "bteup",
          column_mapping: columnMapping,
          options: options
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.detail || "Failed to start bulk job");
      }

      currentJobId = data.job_id;

      // Reveal Step 4 & scroll into view
      step4Card.style.display = "block";
      step4Card.scrollIntoView({ behavior: "smooth" });

      startStatusPolling(currentJobId);

    } catch (err) {
      alert("Could not start processing: " + err.message);
      btnStartBulk.disabled = false;
      btnStartBulk.textContent = "▶ Start Bulk Processing";
    }
  });

  // 4. Status Polling & Real-time Live Updates
  function startStatusPolling(jobId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/process/status/${jobId}`);
        if (!res.ok) return;

        const data = await res.json();
        const job = data.job;

        // Progress bar & metrics
        progressBar.style.width = `${job.percent}%`;
        progressPercentage.textContent = `${job.percent}%`;
        currentStatusBadge.textContent = job.status.toUpperCase();

        if (job.status === "completed") {
          currentStatusBadge.className = "badge badge-success";
        } else if (job.status === "failed") {
          currentStatusBadge.className = "badge badge-fail";
        } else {
          currentStatusBadge.className = "badge badge-info";
        }

        metricTotal.textContent = job.total;
        metricSuccess.textContent = job.successful;
        metricFailed.textContent = job.failed;
        metricSkipped.textContent = job.skipped;

        // Logs terminal
        logTerminal.innerHTML = "";
        job.recent_logs.forEach(msg => {
          const d = document.createElement("div");
          d.textContent = msg;
          logTerminal.appendChild(d);
        });
        logTerminal.scrollTop = logTerminal.scrollHeight;

        // Live Results Table
        renderLiveResults(job.results);

        // Show Retry All Failed button if there are failures
        if (job.failed > 0 && job.status === "completed") {
          btnRetryFailed.style.display = "inline-flex";
        } else {
          btnRetryFailed.style.display = "none";
        }

        // When complete
        if (job.status === "completed" || job.status === "failed") {
          clearInterval(pollInterval);
          btnStartBulk.disabled = false;
          btnStartBulk.textContent = "▶ Start Bulk Processing";

          setupExportLinks(jobId);
          step5Card.style.display = "block";
        }

      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 1000);
  }

  function renderLiveResults(results) {
    liveResultsBody.innerHTML = "";
    results.forEach((r, idx) => {
      const tr = document.createElement("tr");

      // Evaluation status badge
      let statusBadge = `<span class="badge badge-gray">${r.status}</span>`;
      if (r.status === "Success" || r.status === "Cached") {
        statusBadge = `<span class="badge badge-success">${r.status}</span>`;
      } else if (r.status === "Failed") {
        statusBadge = `<span class="badge badge-fail" title="${r.error_message}">Failed</span>`;
      } else if (r.status === "Skipped") {
        statusBadge = `<span class="badge badge-warn" title="${r.error_message}">Skipped</span>`;
      }

      // Marksheet action
      let pdfCell = "-";
      if (r.pdf_path) {
        pdfCell = `<a href="/api/download/${currentJobId}/pdf?enrollment=${encodeURIComponent(r.enrollment)}" target="_blank" class="btn btn-secondary btn-sm">View Marksheet</a>`;
      }

      // Individual retry button
      let actionCell = "-";
      if (r.status === "Failed") {
        actionCell = `<button class="btn btn-secondary btn-sm btn-retry-single" data-enrollment="${r.enrollment}">🔄 Retry</button>`;
      }

      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td><strong>${r.enrollment}</strong></td>
        <td>${r.student_name || "-"}</td>
        <td>${r.total_obtained ? `${r.total_obtained} / ${r.total_max}` : "-"}</td>
        <td>${r.overall_percentage ? `${r.overall_percentage}%` : "-"}</td>
        <td>${r.result_status || "-"}</td>
        <td>${statusBadge}</td>
        <td>${pdfCell}</td>
        <td>${actionCell}</td>
      `;
      liveResultsBody.appendChild(tr);
    });

    // Attach retry listeners
    document.querySelectorAll(".btn-retry-single").forEach(btn => {
      btn.addEventListener("click", async () => {
        const enr = btn.getAttribute("data-enrollment");
        btn.disabled = true;
        btn.textContent = "Retrying...";
        try {
          await fetch(`/api/process/retry/${currentJobId}/${encodeURIComponent(enr)}`, { method: "POST" });
          startStatusPolling(currentJobId);
        } catch (e) {
          alert("Retry failed to launch: " + e.message);
        }
      });
    });
  }

  // Retry all failed
  btnRetryFailed.addEventListener("click", async () => {
    btnRetryFailed.disabled = true;
    btnRetryFailed.textContent = "Initiating retry...";
    try {
      await fetch(`/api/process/retry-failed/${currentJobId}`, { method: "POST" });
      startStatusPolling(currentJobId);
    } catch (e) {
      alert("Retry failed: " + e.message);
    } finally {
      btnRetryFailed.disabled = false;
    }
  });

  // 5. Setup Export Download Links
  function setupExportLinks(jobId) {
    btnDownloadConsolidated.href = `/api/download/${jobId}/consolidated_excel`;
    btnDownloadSubjectWise.href = `/api/download/${jobId}/subject_excel`;
    btnDownloadMarksheetsZip.href = `/api/download/${jobId}/marksheets_zip`;
    btnDownloadCompleteZip.href = `/api/download/${jobId}/complete_zip`;
  }

  // Reset
  btnResetApp.addEventListener("click", () => {
    if (confirm("Reset current batch and prepare a new processing job?")) {
      window.location.reload();
    }
  });

});
