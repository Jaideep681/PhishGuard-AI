import { waitForAuth } from "./firebase.js";
const API_BASE_URL = "";
const qrForm = document.getElementById("qrForm");
const qrImage = document.getElementById("qrImage");
const scanButton = document.getElementById("scanButton");
const statusBox = document.getElementById("status");
const previewBox = document.getElementById("previewBox");
const imagePreview = document.getElementById("imagePreview");
const resultBox = document.getElementById("resultBox");

let previewObjectUrl = null;

// Obtain the signed-in user's Firebase ID token.
async function getAuthToken() {
    const user = await waitForAuth();

    if (!user) {
        window.location.replace("PhishLogin.html");
        throw new Error("Please sign in with Google first.");
    }

    return await user.getIdToken();
}

// Display selected image preview.
qrImage.addEventListener("change", function () {
    resultBox.style.display = "none";
    statusBox.textContent = "";

    const file = this.files[0];

    if (previewObjectUrl) {
        URL.revokeObjectURL(previewObjectUrl);
        previewObjectUrl = null;
    }

    if (!file) {
        previewBox.style.display = "none";
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        this.value = "";
        previewBox.style.display = "none";
        statusBox.textContent = "Image size must not exceed 10 MB.";
        return;
    }

    previewObjectUrl = URL.createObjectURL(file);
    imagePreview.src = previewObjectUrl;
    previewBox.style.display = "block";
});

qrForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const file = qrImage.files[0];

    if (!file) {
        statusBox.textContent = "Please select a QR code image.";
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        statusBox.textContent = "Image size must not exceed 10 MB.";
        return;
    }

    scanButton.disabled = true;
    scanButton.textContent = "Scanning...";
    statusBox.textContent = "Decoding QR code. Please wait...";
    resultBox.style.display = "none";

    try {
        const token = await getAuthToken();

        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(
            API_BASE_URL + "/api/qr-scan",
            {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + token
                },
                body: formData
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
                result.message || "QR code scanning failed."
            );
        }

        const data = result.data;

        document.getElementById("scanStatus").textContent =
            data.success ? "Completed" : "Not completed";

        document.getElementById("qrDetected").textContent =
            data.success ? "Yes" : "No";

        document.getElementById("contentType").textContent =
            data.is_url ? "Website URL" : "Plain Text";

        document.getElementById("decodedContent").textContent =
            data.decoded_text || data.message || "No content decoded.";

        const decodedLink = document.getElementById("decodedLink");

        // Only show a link when the backend identifies an HTTP(S) URL.
        decodedLink.hidden = true;
        decodedLink.removeAttribute("href");

        if (data.is_url && data.url) {
            try {
                const parsedUrl = new URL(data.url);

                if (["http:", "https:"].includes(parsedUrl.protocol)) {
                    decodedLink.href = parsedUrl.href;
                    decodedLink.hidden = false;
                }
            } catch {
                // Invalid URL: display decoded text without linking.
            }
        }

        resultBox.style.display = "block";
        statusBox.textContent = "QR code processing completed.";

    } catch (error) {
        statusBox.textContent = error.message ||
            "Unable to connect to the QR scanning service.";

    } finally {
        scanButton.disabled = false;
        scanButton.textContent = "Scan QR Code";
    }
});

window.addEventListener("beforeunload", function () {
    if (previewObjectUrl) {
        URL.revokeObjectURL(previewObjectUrl);
    }
});