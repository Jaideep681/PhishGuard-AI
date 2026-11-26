import { waitForAuth } from "./firebase.js";
const API_BASE_URL = "";
const PAGE_SIZE = 10;
let currentOffset = 0;

// Get the ID token from the shared Firebase authentication session.
async function getAuthToken() {
    const user = await waitForAuth();

    if (!user) {
        window.location.replace("PhishLogin.html");
        throw new Error("Please sign in with Google first.");
    }

    return await user.getIdToken();
}

async function apiRequest(url, options = {}) {
    const token = await getAuthToken();

    return fetch(API_BASE_URL + url, {
        ...options,
        headers: {
            ...(options.headers || {}),
            "Authorization": "Bearer " + token
        }
    });
}

function displayResult(result) {
    const value = String(result || "Unknown");
    const normalized = value.toLowerCase();

    let cssClass = "other";

    if (normalized.includes("legitimate")) {
        cssClass = "legitimate";
    } else if (normalized.includes("phishing")) {
        cssClass = "phishing";
    }

    return `<span class="result ${cssClass}">${value}</span>`;
}

async function loadHistory() {
    const status = document.getElementById("status");
    const tableBody = document.getElementById("historyTableBody");

    status.textContent = "Loading scan history...";
    tableBody.replaceChildren();

    try {
        const response = await apiRequest(
            `/api/history?limit=${PAGE_SIZE}&offset=${currentOffset}`
        );

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || "Unable to load scan history.");
        }

        const records = result.data;

        if (!Array.isArray(records) || records.length === 0) {
            status.textContent = "No scan history found.";
            updatePagination(0);
            return;
        }

        status.textContent = "";

        records.forEach(scan => {
            const row = document.createElement("tr");
            const scanId = scan.scan_id;
            const scannedUrl = scan.scanned_url || "N/A";
            const scanResult = scan.scan_result ||
                scan.predicted_label || "Unknown";
            const confidence = scan.confidence_score;
            const scanDate = scan.scan_date || scan.timestamp || "N/A";

            const cells = [
                scanId,
                scannedUrl,
                null,
                confidence == null ? "N/A" : confidence + "%",
                scanDate
            ];

            cells.forEach((value, index) => {
                const cell = document.createElement("td");

                if (index === 2) {
                    cell.innerHTML = displayResult(scanResult);
                } else {
                    cell.textContent = value;
                }
                row.appendChild(cell);
            });

            const actionCell = document.createElement("td");
            const deleteButton = document.createElement("button");
            deleteButton.textContent = "Delete";
            deleteButton.className = "delete-btn";
            deleteButton.addEventListener("click", () => {
                deleteScan(scanId);
            });
            actionCell.appendChild(deleteButton);
            row.appendChild(actionCell);

            tableBody.appendChild(row);
        });
        updatePagination(records.length);
    }
    catch (error) {
        status.textContent = error.message;
        updatePagination(0);
    }
}

function updatePagination(recordCount) {
    document.getElementById("previousBtn").disabled =
        currentOffset === 0;

    document.getElementById("nextBtn").disabled =
        recordCount < PAGE_SIZE;

    document.getElementById("pageNumber").textContent =
        `Page ${Math.floor(currentOffset / PAGE_SIZE) + 1}`;
}

async function deleteScan(scanId) {
    if (!confirm("Are you sure you want to delete this scan record?")) {
        return;
    }

    try {
        const response = await apiRequest(
            `/api/history/${encodeURIComponent(scanId)}`,
            { method: "DELETE" }
        );

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || "Unable to delete scan.");
        }

        await loadHistory();

    } catch (error) {
        alert(error.message);
    }
}

document.getElementById("previousBtn").addEventListener("click", () => {
    if (currentOffset >= PAGE_SIZE) {
        currentOffset -= PAGE_SIZE;
        loadHistory();
    }
});

document.getElementById("nextBtn").addEventListener("click", () => {
    currentOffset += PAGE_SIZE;
    loadHistory();
});

loadHistory();