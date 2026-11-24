import { initializeApp, getApp, getApps } from
    "https://www.gstatic.com/firebasejs/13.4.0/firebase-app.js";
import {
    getAuth,
    GoogleAuthProvider,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/13.4.0/firebase-auth.js";

import { getFirestore } from
    "https://www.gstatic.com/firebasejs/13.4.0/firebase-firestore.js";

const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "phishguard-ai-2ba75.firebaseapp.com",
    projectId: "phishguard-ai-2ba75",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
};

// Prevent duplicate Firebase initialization.
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();

// Wait until Firebase restores the saved login session.
export function waitForAuth() {
    return new Promise((resolve) => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            unsubscribe();
            resolve(user);
        });
    });
}