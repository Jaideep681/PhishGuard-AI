import { waitForAuth } from "./firebase.js";
// Flask backend address.
const API_BASE_URL = "";
const dnsForm = document.getElementById("dnsForm");
const urlInput = document.getElementById("urlInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const formStatus = document.getElementById("formStatus");
const resultsSection = document.getElementById("resultsSection");

// Read the signed-in user from the shared Firebase module.
async function getAuthToken() {
    const user = await waitForAuth();

    if (!user) {
        window.location.replace("PhishLogin.html");
        throw new Error("Please sign in with Google first.");
    }

    return await user.getIdToken();
}

function showStatus(message, type) {
    formStatus.textContent = message;
    formStatus.className = "status " + type;
}

function clearStatus() {
    formStatus.textContent = "";
    formStatus.className = "status";
}

function createTextElement(tag, className, value) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    element.textContent = value;
    return element;
}

function displayRecords(records) {
    const container = document.getElementById("recordsContainer");
    container.replaceChildren();

    const recordTypes = ["A", "AAAA", "MX", "NS", "TXT"];

    recordTypes.forEach(type => {
        const record = records?.[type] || {
            status: "unknown",
            records: [],
            error: null
        };

        const card = document.createElement("div");
        card.className = "record-card";

        card.appendChild(createTextElement("h3", "", type + " Records"));

        card.appendChild(
            createTextElement(
                "p",
                "record-status",
                "Status: " + (record.status || "unknown")
            )
        );

        const list = document.createElement("ul");
        list.className = "record-list";

        if (Array.isArray(record.records) && record.records.length > 0) {
            record.records.forEach(value => {
                list.appendChild(createTextElement("li", "", String(value)));
            });
        } else {
            list.appendChild(
                createTextElement("li", "", "No records returned.")
            );
        }

        card.appendChild(list);

        if (record.error) {
            card.appendChild(
                createTextElement("p", "record-error", record.error)
            );
        }

        container.appendChild(card);
    });
}

function displayIndicators(indicators) {
    const container = document.getElementById("indicatorsContainer");
    container.replaceChildren();

    if (!Array.isArray(indicators) || indicators.length === 0) {
        container.appendChild(
            createTextElement("p", "hint", "No additional indicators were returned.")
        );
        return;
    }

    indicators.forEach(item => {
        const severity = String(item.severity || "informational").toLowerCase();

        const card = document.createElement("div");
        card.className = "indicator " +
            (severity === "warning" ? "warning" : "informational");

        card.appendChild(
            createTextElement("span", "severity", severity)
        );

        card.appendChild(
            createTextElement("strong", "", item.name || "DNS indicator")
        );

        card.appendChild(
            createTextElement("p", "", item.detail || "")
        );

        container.appendChild(card);
    });
}

function displayResults(data) {
    document.getElementById("hostnameValue").textContent =
        data.hostname || "Not available";

    document.getElementById("inputValue").textContent =
        data.input_url || "Not available";

    document.getElementById("schemeValue").textContent =
        data.scheme || "Not applicable";

    document.getElementById("ipValue").textContent =
        data.is_ip_address === true ? "Yes" :
            data.is_ip_address === false ? "No" : "Not available";

    document.getElementById("timeValue").textContent =
        data.analysis_time_utc || "Not available";

    document.getElementById("analysisMessage").textContent =
        data.message || "DNS analysis completed.";

    displayRecords(data.records || {});
    displayIndicators(data.indicators || []);

    resultsSection.hidden = false;
}

dnsForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const url = urlInput.value.trim();

    if (!url) {
        showStatus("Please enter a website URL or domain.", "error");
        return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing...";
    clearStatus();
    resultsSection.hidden = true;

    try {
        const token = await getAuthToken();

        const response = await fetch(
            API_BASE_URL + "/api/dns-analysis",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token
                },
                body: JSON.stringify({ url: url })
            }
        );

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(
                result.message || "DNS analysis could not be completed."
            );
        }

        const data = result.data;

        if (!data || typeof data !== "object") {
            throw new Error("The backend returned an unexpected response.");
        }

        // The analyzer may return success:false for invalid input.
        // Display its validation message without treating it as a DNS result.
        if (data.success === false) {
            throw new Error(data.message || "The supplied domain could not be analyzed.");
        }

        displayResults(data);
        showStatus(result.message || "DNS analysis completed successfully.", "success");

    } catch (error) {
        showStatus(
            error.message || "Something went wrong during DNS analysis.",
            "error"
        );
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze DNS";
    }
});