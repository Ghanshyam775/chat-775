document.addEventListener("DOMContentLoaded", function() {
  // DOM Elements for chat.html
  const contactsList = document.getElementById("contactsList");
  const chatHeaderName = document.getElementById("chatHeaderName");
  const sendBtn = document.getElementById("sendBtn");
  const messageInput = document.getElementById("messageInput");
  const messagesDiv = document.getElementById("messages");
  const logoutBtn = document.getElementById("logoutBtn");
  const voiceCallBtn = document.getElementById("voiceCallBtn");
  const videoCallBtn = document.getElementById("videoCallBtn");
  const deleteChatBtn = document.getElementById("deleteChatBtn");
  const attachBtn = document.getElementById("attachBtn");
  const mediaInput = document.getElementById("mediaInput");
  const toastContainer = document.getElementById("toastContainer");

  let currentUser = null;
  let currentChatId = null;
  let currentChatContact = null;
  let usersMap = {}; // Map from uid to user object (including username and profile_image_url)

  // Request notification permission
  if ("Notification" in window && Notification.permission !== "granted") {
    Notification.requestPermission();
  }

  // Listen for auth state changes
  firebase.auth().onAuthStateChanged(user => {
    if (user) {
      currentUser = user;
      loadContacts();
    } else {
      window.location.href = "login";
    }
  });

  // Logout handler
  logoutBtn.addEventListener("click", () => {
    firebase.auth().signOut().then(() => {
      window.location.href = "login";
    });
  });

  // Load contacts from /api/users
  function loadContacts() {
    fetch("/api/users")
      .then(response => response.json())
      .then(data => {
        data.forEach(user => {
          usersMap[user.uid] = user;
        });
        renderContacts(data);
      })
      .catch(error => console.error("Error loading contacts:", error));
  }

  // Render contacts (display profile image and username; exclude current user)
  function renderContacts(users) {
    contactsList.innerHTML = "";
    users.forEach(user => {
      if (user.uid === currentUser.uid) return;
      const li = document.createElement("li");
      li.className = "list-group-item list-group-item-action";
      li.style.cursor = "pointer";
      const imgSrc = user.profile_image_url || "https://via.placeholder.com/30";
      li.innerHTML = `<img src="${imgSrc}" class="contact-img" alt="Profile"> ${user.username}`;
      li.setAttribute("data-uid", user.uid);
      li.addEventListener("click", () => {
        currentChatContact = user;
        currentChatId = [currentUser.uid, user.uid].sort().join("_");
        chatHeaderName.textContent = user.username;
        loadMessages();
      });
      contactsList.appendChild(li);
    });
  }

  // Send message (text and optional media)
  sendBtn.addEventListener("click", () => {
    const text = messageInput.value;
    const mediaUrl = sendBtn.getAttribute("data-media-url") || "";
    if (!text && !mediaUrl) return;
    db.collection("chats").doc(currentChatId).collection("messages").add({
      senderId: currentUser.uid,
      text: text,
      media_url: mediaUrl,
      timestamp: firebase.firestore.FieldValue.serverTimestamp(),
      deleted: false,
      reactions: {}
    }).then(() => {
      messageInput.value = "";
      sendBtn.removeAttribute("data-media-url");
    }).catch(error => {
      console.error("Error sending message:", error);
    });
  });

  // Load messages with auto-scroll and notifications
  function loadMessages() {
    db.collection("chats").doc(currentChatId).collection("messages")
      .orderBy("timestamp")
      .onSnapshot(snapshot => {
        messagesDiv.innerHTML = "";
        snapshot.forEach(doc => {
          const message = doc.data();
          if (message.deleted) return;
          const messageElem = document.createElement("div");
          messageElem.className = "message-card mb-2 " + (message.senderId === currentUser.uid ? "you" : "");
          let profileImgHtml = "";
          if (usersMap[message.senderId] && usersMap[message.senderId].profile_image_url) {
              profileImgHtml = `<img src="${usersMap[message.senderId].profile_image_url}" class="contact-img" alt="Profile"> `;
          } else {
              profileImgHtml = `<img src="https://via.placeholder.com/30" class="contact-img" alt="Profile"> `;
          }
          const senderName = message.senderId === currentUser.uid ? "You" : (usersMap[message.senderId]?.username || "Unknown");
          let contentHtml = `${profileImgHtml}<strong>${senderName}:</strong> `;
          if (message.text) contentHtml += message.text;
          if (message.media_url) {
            contentHtml += `<br><img src="${message.media_url}" alt="Media" class="img-fluid" style="max-width:200px;">`;
          }
          contentHtml += `<div class="mt-1 message-actions">
              <button class="deleteBtn" data-id="${doc.id}" title="Delete"><i class="bi bi-trash"></i></button>
              <button class="forwardBtn" data-id="${doc.id}" data-text="${message.text}" title="Forward"><i class="bi bi-arrow-right-square"></i></button>
              <button class="reactBtn" data-id="${doc.id}" title="React"><i class="bi bi-emoji-smile"></i></button>
              <span class="reactionDisplay">${formatReactions(message.reactions)}</span>
            </div>`;
          messageElem.innerHTML = contentHtml;
          messagesDiv.appendChild(messageElem);
          // Show desktop notification if document is hidden and message is not from current user
          if (document.hidden && message.senderId !== currentUser.uid) {
            showDesktopNotification(`${senderName}: ${message.text}`);
          }
        });
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        addActionEventListeners();
      });
  }

  // Format reactions into a string
  function formatReactions(reactions) {
    let result = "";
    if (reactions) {
      for (const uid in reactions) {
        result += `${reactions[uid]} `;
      }
    }
    return result;
  }

  // Add event listeners for message action buttons
  function addActionEventListeners() {
    document.querySelectorAll(".deleteBtn").forEach(btn => {
      btn.addEventListener("click", function() {
        const messageId = this.getAttribute("data-id");
        if (confirm("Are you sure you want to delete this message?")) {
          fetch("/api/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ chatId: currentChatId, messageId: messageId })
          })
          .then(response => response.json())
          .then(data => console.log(data))
          .catch(error => console.error("Error deleting message:", error));
        }
      });
    });
    document.querySelectorAll(".forwardBtn").forEach(btn => {
      btn.addEventListener("click", function() {
        const messageId = this.getAttribute("data-id");
        fetch("/api/forward", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ originalChatId: currentChatId, messageId: messageId, targetChatId: currentChatId })
        })
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.error("Error forwarding message:", error));
      });
    });
    document.querySelectorAll(".reactBtn").forEach(btn => {
      btn.addEventListener("click", function() {
        const messageId = this.getAttribute("data-id");
        const reaction = prompt("Enter your reaction (e.g., 👍):");
        if (reaction) {
          fetch("/api/react", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ chatId: currentChatId, messageId: messageId, userId: currentUser.uid, reaction: reaction })
          })
          .then(response => response.json())
          .then(data => console.log(data))
          .catch(error => console.error("Error reacting to message:", error));
        }
      });
    });
  }

  // Attach file (media) handler
  attachBtn.addEventListener("click", () => {
    mediaInput.click();
  });

  mediaInput.addEventListener("change", function(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    fetch("/api/upload", {
      method: "POST",
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert("File upload error: " + data.error);
      } else {
        sendBtn.setAttribute("data-media-url", data.file_url);
        alert("File attached. Press Send to deliver the message.");
      }
    })
    .catch(error => alert("File upload error: " + error.message));
  });

  // Delete entire chat handler
  deleteChatBtn.addEventListener("click", () => {
    if (confirm("Are you sure you want to delete the entire chat? This cannot be undone.")) {
      fetch("/api/delete_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chatId: currentChatId })
      })
      .then(response => response.json())
      .then(data => {
        alert("Chat deleted.");
        messagesDiv.innerHTML = "";
      })
      .catch(error => console.error("Error deleting chat:", error));
    }
  });

  // Voice Call button handler
  voiceCallBtn.addEventListener("click", () => {
    if (!currentChatContact) return;
    new bootstrap.Modal(document.getElementById("voiceCallModal")).show();
  });

  // Video Call button handler (basic local video setup)
  videoCallBtn.addEventListener("click", () => {
    if (!currentChatContact) return;
    const localVideo = document.getElementById("localVideo");
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      .then(stream => {
        localVideo.srcObject = stream;
        new bootstrap.Modal(document.getElementById("videoCallModal")).show();
      })
      .catch(error => {
        console.error("Error accessing media devices:", error);
      });
  });

  // Desktop notification function using Notification API
  function showDesktopNotification(message) {
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("New Message", { body: message });
    } else {
      showToast(message);
    }
  }

  // Toast notification function using Bootstrap Toasts
  function showToast(message) {
    const toastEl = document.createElement("div");
    toastEl.className = "toast align-items-center text-bg-primary border-0";
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>`;
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    toast.show();
    toastEl.addEventListener("hidden.bs.toast", () => {
      toastEl.remove();
    });
  }
});
