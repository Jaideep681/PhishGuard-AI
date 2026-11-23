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
    apiKey: "AIzaSyCbI-m6sVVecgEb0uM6mex0jwlcFAyMCqI",
    authDomain: "phishguard-ai-2ba75.firebaseapp.com",
    projectId: "phishguard-ai-2ba75",
    storageBucket: "phishguard-ai-2ba75.firebasestorage.app",
    messagingSenderId: "161577128907",
    appId: "1:161577128907:web:3ee1737f290ece75ee9c4e"
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