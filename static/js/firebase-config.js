// Replace these config values with your Firebase project's details
const firebaseConfig = {
    apiKey: "AIzaSyDTyEpZjvcTDB3ziSkJDXb7hI_742mkndE",
    authDomain: "chat-775-3df66.firebaseapp.com",
    projectId: "chat-775-3df66",
    storageBucket: "chat-775-3df66.firebasestorage.app",
    messagingSenderId: "717450483437",
    appId: "1:717450483437:web:cf575588fb9c64018edee4",
  
  };
  
  // Initialize Firebase
  firebase.initializeApp(firebaseConfig);
  const auth = firebase.auth();
  const db = firebase.firestore();
  