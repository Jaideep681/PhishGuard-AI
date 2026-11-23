// PHISHGUARD AI - GOOGLE LOGIN
// Firebase Authentication + Cloud Firestore
import { 
    auth, 
    db, 
    waitForAuth, 
    googleProvider } from "./firebase.js";
import {
    signInWithPopup,
    setPersistence,
    browserLocalPersistence
} from "https://www.gstatic.com/firebasejs/13.4.0/firebase-auth.js";
import {
    doc,
    getDoc,
    setDoc,
    serverTimestamp
} from "https://www.gstatic.com/firebasejs/13.4.0/firebase-firestore.js";

// Firebase is initialized once in firebase.js and shared by all pages.

// PAGE ELEMENTS
const googleSignInBtn = document.getElementById("googleSignInBtn");
const loginStatus = document.getElementById("loginStatus");
const dashboardURL = document.body.dataset.dashboardUrl;

// If a previous Google session is still active, skip the login screen.
waitForAuth().then(user => {
    if (user) {
        window.location.replace(dashboardURL || "Dashboard.html");
    }
});

// 4. DISPLAY STATUS
function showStatus(message, isError = false) {
    loginStatus.textContent = message;
    loginStatus.style.color = isError? "#dc2626": "#15803d";
}

// 5. SAVE USER PROFILE IN FIRESTORE
async function saveUserProfile(user) {
    const userRef = doc(db, "users", user.uid);
    const existingUser = await getDoc(userRef);
    const userData = {
        uid: user.uid,
        fullName: user.displayName || "",
        email: user.email || "",
        profilePicture: user.photoURL || "",
        provider: "Google",
        lastLoginAt: serverTimestamp()
    };
    if (!existingUser.exists()) {
        userData.createdAt = serverTimestamp();
    }
    await setDoc(userRef, userData, { merge: true });
}

// 6. GOOGLE SIGN-IN PROCESS
googleSignInBtn.addEventListener("click", async function () {
    try {
        googleSignInBtn.disabled = true;
        googleSignInBtn.textContent = "Connecting to Google...";
        showStatus("Please wait. Authenticating your account...");

        // Keep the user signed in across browser sessions.
        await setPersistence(auth, browserLocalPersistence);

        // Open Google authentication popup.
        const result = await signInWithPopup(auth, googleProvider);
        const user = result.user;

        // Save or update the user's Firestore profile.
        await saveUserProfile(user);
        showStatus("Login successful! Redirecting to dashboard...");

        // Redirect after successful authentication and profile save.
        window.location.replace(dashboardURL);
    } catch (error) {
        console.error("Google Sign-In Error:", error);
        let message = "Unable to sign in. Please try again.";
        switch (error.code) {
            case "auth/popup-closed-by-user":
                message = "Google sign-in was cancelled.";
                break;

            case "auth/popup-blocked":
                message = "Your browser blocked the Google sign-in popup. Allow popups and try again.";
                break;

            case "auth/unauthorized-domain":
                message = "This website domain is not authorized in Firebase.";
                break;

            case "auth/network-request-failed":
                message = "Network error. Please check your internet connection.";
                break;

            case "permission-denied":
            case "firestore/permission-denied":
                message = "Unable to save your profile. Please check Firestore security rules.";
                break;

            default:
                message = error.message || message;
        }
        showStatus(message, true);
        googleSignInBtn.disabled = false;
        googleSignInBtn.textContent = "Continue with Google";
    }
});