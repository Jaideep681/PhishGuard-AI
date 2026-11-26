import { auth, waitForAuth } from "./firebase.js";
const API_BASE = "http://127.0.0.1:5000";
const userEmail = document.getElementById("userEmail");
const historyMessage = document.getElementById("historyMessage");

// Firebase authentication helper
let signedInUser = null;

async function getAuthToken() {
    const user = signedInUser || await waitForAuth();

    if (!user) {
        window.location.replace("PhishLogin.html");
        throw new Error("Please sign in with Google first.");
    }

    return await user.getIdToken();
}

// Make an authenticated API request
async function apiRequest(endpoint) {
    const token = await getAuthToken();

    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    });

    const result = await response.json();

    if (!response.ok || result.success === false) {
        throw new Error(result.message || "Unable to load dashboard data.");
    }

    return result.data;
}

// Safely format values
function displayNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toLocaleString() : "0";
}

// Load statistics
async function loadStatistics() {
    try {
        const data = await apiRequest("/api/statistics");

        // These fields may need adjustment to match the exact
        // structure returned by your statistics API.
        const stats = data.statistics || data;

        document.getElementById("totalScans").textContent =
            displayNumber(stats.total_scans ?? stats.totalScans);

        document.getElementById("phishingScans").textContent =
            displayNumber(stats.phishing_scans ?? stats.phishingScans);

        document.getElementById("legitimateScans").textContent =
            displayNumber(stats.legitimate_scans ?? stats.legitimateScans);

    } catch (error) {
        document.getElementById("totalScans").textContent = "—";
        document.getElementById("phishingScans").textContent = "—";
        document.getElementById("legitimateScans").textContent = "—";

        console.error("Statistics error:", error);
    }
}

// Normalize the prediction label for display
function getResultLabel(value) {
    const result = String(value ?? "").toLowerCase();

    if (
        result.includes("phish") ||
        result === "0" ||
        result.includes("class_0")
    ) {
        return {
            label: "Phishing",
            className: "phishing"
        };
    }

    if (
        result.includes("legitimate") ||
        result.includes("safe") ||
        result === "1" ||
        result.includes("class_1")
    ) {
        return {
            label: "Legitimate",
            className: "legitimate"
        };
    }

    return {
        label: value || "Unknown",
        className: "other"
    };
}

// Load recent scans
async function loadRecentScans() {
    try {
        const data = await apiRequest("/api/history");

        const scans = Array.isArray(data)
            ? data
            : (data.history || data.scans || data.records || []);

        const historyBody = document.getElementById("historyBody");
        historyBody.replaceChildren();

        if (!scans.length) {
            historyMessage.textContent = "No URL scans found yet.";
            historyMessage.hidden = false;
            document.getElementById("historyTable").hidden = true;
            return;
        }

        // Display the latest five records
        scans.slice(0, 5).forEach(scan => {
            const row = document.createElement("tr");

            const urlCell = document.createElement("td");
            urlCell.textContent = scan.scanned_url || scan.url || "—";

            const resultCell = document.createElement("td");
            const result = getResultLabel(
                scan.scan_result ??
                scan.predicted_label ??
                scan.result
            );

            const status = document.createElement("span");
            status.className = `status ${result.className}`;
            status.textContent = result.label;
            resultCell.appendChild(status);

            const confidenceCell = document.createElement("td");
            const confidence = scan.confidence_score ?? scan.confidence;

            confidenceCell.textContent =
                confidence === undefined || confidence === null
                    ? "—"
                    : `${Number(confidence).toFixed(2)}%`;

            const dateCell = document.createElement("td");
            const dateValue = scan.scan_date || scan.timestamp;

            dateCell.textContent = dateValue
                ? new Date(dateValue).toLocaleString()
                : "—";

            row.append(urlCell, resultCell, confidenceCell, dateCell);
            historyBody.appendChild(row);
        });

        historyMessage.hidden = true;
        document.getElementById("historyTable").hidden = false;

    } catch (error) {
        console.error("History error:", error);
        historyMessage.textContent = error.message;
        historyMessage.classList.add("error-message");
        historyMessage.hidden = false;
    }
}

// Sign out
document.getElementById("logoutBtn").addEventListener("click", async () => {
    try {
        const { signOut } = await import(
            "https://www.gstatic.com/firebasejs/13.4.0/firebase-auth.js"
        );

        await signOut(auth);
        window.location.replace("PhishLogin.html");

    } catch (error) {
        alert(error.message || "Unable to sign out.");
    }
});

// Initialize dashboard after Firebase authentication is ready
async function initializeDashboard() {
    try {
        const user = await waitForAuth();

        if (!user) {
            window.location.replace("PhishLogin.html");
            return;
        }

        signedInUser = user;
        userEmail.textContent = user.email || "Google account signed in";

        await Promise.all([
            loadStatistics(),
            loadRecentScans()
        ]);

    } catch (error) {
        userEmail.textContent = error.message;

        document.getElementById("totalScans").textContent = "—";
        document.getElementById("phishingScans").textContent = "—";
        document.getElementById("legitimateScans").textContent = "—";

        historyMessage.textContent = error.message;
        historyMessage.classList.add("error-message");
    }
}

initializeDashboard();