// Replace these config values with your Firebase project's details
const firebaseConfig = {
  apiKey: "AIzaSyA1cluOm4xb4x97aaN9KtxBdUlGorc_19k",
  authDomain: "pro-chat-775.firebaseapp.com",
  projectId: "pro-chat-775",
  storageBucket: "pro-chat-775.firebasestorage.app",
  messagingSenderId: "603942090352",
  appId: "1:603942090352:web:93ec63d30fc906328066b5",
  measurementId: "G-2XH0488MMY"
};
  

  
  // Initialize Firebase
  firebase.initializeApp(firebaseConfig);
  const auth = firebase.auth();
  const db = firebase.firestore();
  