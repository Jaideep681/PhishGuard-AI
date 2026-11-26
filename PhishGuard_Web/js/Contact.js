const API_BASE_URL = "";
/* 
* After Vercel deployment change this url to "https://phishguard-ai.onrender.com"
*/
document.getElementById("contactForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const form = this;
    const button = document.getElementById("submitBtn");
    const status = document.getElementById("formStatus");
    const formData = {
        fullName: form.fullName.value.trim(),
        email: form.email.value.trim(),
        subject: form.subject.value,
        message: form.message.value.trim(),
        website: form.website.value
    };
    button.disabled = true;
    button.textContent = "Sending...";
    status.textContent = "";
    try {
        const response = await fetch(`${API_BASE_URL}/api/contact`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
        });
        const responseText = await response.text();

        let result;

        try {
            result = JSON.parse(responseText);
        } catch {
            throw new Error(
                `Server returned an invalid response (HTTP ${response.status}). Check the Flask backend.`
            );
        }
        if (!response.ok || !result.success) {
            throw new Error(result.message || "Message could not be sent.");
        }
        status.textContent = result.message;
        form.reset();
    } catch (error) {
        status.textContent = error.message || "Something went wrong. Please try again.";
    } finally {
        button.disabled = false;
        button.textContent = "Submit Query";
    }
});
