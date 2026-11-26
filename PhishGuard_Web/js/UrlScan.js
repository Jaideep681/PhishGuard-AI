import { waitForAuth } from "./firebase.js";
const API_BASE_URL = "http://127.0.0.1:5000";
const scanForm = document.getElementById("scanForm");
const scanButton = document.getElementById("scanButton");
const statusBox = document.getElementById("status");
const resultBox = document.getElementById("resultBox");

// Obtain the Firebase ID token of the signed-in user.
async function getAuthToken() {
    const user = await waitForAuth();

    if (!user) {
        window.location.replace("PhishLogin.html");
        throw new Error("Please sign in with Google first.");
    }

    return await user.getIdToken();
}

function setText(id, value) {
    document.getElementById(id).textContent =
        value == null ? "N/A" : String(value);
}

function setProbability(classKey, value) {
    const percentage = Number(value) * 100;
    const safePercentage = Number.isFinite(percentage)
        ? Math.max(0, Math.min(100, percentage))
        : 0;

    setText(classKey + "Value", safePercentage.toFixed(2) + "%");

    document.getElementById(classKey + "Bar").style.width =
        safePercentage + "%";
}

function showResult(data) {
    setText("scannedUrl", data.scanned_url);
    setText("confidence",
        data.confidence_score == null
            ? "N/A"
            : data.confidence_score + "%"
    );
    setText("scanId", data.scan_id);
    setText("featureCount", data.extracted_feature_count);
    setText("modelFeatures", data.model_input_feature_count);
    setText("scanStatus", data.status);

    const prediction = document.getElementById("prediction");
    const label = String(data.predicted_label || "Unknown");

    prediction.textContent = label;
    prediction.className = "prediction unknown";

    if (label.toLowerCase().includes("legitimate")) {
        prediction.className = "prediction legitimate";
    } else if (label.toLowerCase().includes("phishing")) {
        prediction.className = "prediction phishing";
    }

    const probabilities = data.class_probabilities || {};

    setProbability("class0", probabilities["0"]);
    setProbability("class1", probabilities["1"]);

    resultBox.style.display = "block";
}

scanForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const url = document.getElementById("urlInput").value.trim();

    if (!url) {
        statusBox.textContent = "Please enter a website URL.";
        return;
    }

    scanButton.disabled = true;
    scanButton.textContent = "Scanning...";
    statusBox.textContent = "Analyzing the URL. Please wait...";
    resultBox.style.display = "none";

    try {
        const token = await getAuthToken();

        const response = await fetch(
            API_BASE_URL + "/api/scan",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token
                },
                body: JSON.stringify({ url: url })
            }
        );

        const responseText = await response.text();
        let result;

        try {
            result = JSON.parse(responseText);
        } catch {
            throw new Error(
                "The server returned an invalid response. Check Flask."
            );
        }

        if (!response.ok || !result.success) {
            throw new Error(
                result.message || "URL scanning failed."
            );
        }

        showResult(result.data);
        statusBox.textContent =
            "URL analysis completed successfully.";

    } catch (error) {
        statusBox.textContent = error.message ||
            "Unable to connect to the scanning service.";

    } finally {
        scanButton.disabled = false;
        scanButton.textContent = "Scan URL";
    }
});