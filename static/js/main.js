document.addEventListener("DOMContentLoaded", function() {
    // DOM Elements (for chat.html)
    const contactsList = document.getElementById("contactsList");
    const chatHeaderName = document.getElementById("chatHeaderName");
    const sendBtn = document.getElementById("sendBtn");
    const messageInput = document.getElementById("messageInput");
    const messagesDiv = document.getElementById("messages");
    const logoutBtn = document.getElementById("logoutBtn");
    const voiceCallBtn = document.getElementById("voiceCallBtn");
    const videoCallBtn = document.getElementById("videoCallBtn");
    const voiceCallName = document.getElementById("voiceCallName");
    const videoCallName = document.getElementById("videoCallName");
    const toastContainer = document.getElementById("toastContainer");
  
    let currentUser = null;
    let currentChatId = null;
    let currentChatContact = null;
    let usersMap = {}; // Map from uid to username
  
    // Check auth state and redirect if not logged in
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
            usersMap[user.uid] = user.username;
          });
          renderContacts(data);
        })
        .catch(error => console.error("Error loading contacts:", error));
    }
  
    // Render contacts (exclude current user)
    function renderContacts(users) {
      contactsList.innerHTML = "";
      users.forEach(user => {
        if (user.uid === currentUser.uid) return;
        const li = document.createElement("li");
        li.className = "list-group-item list-group-item-action";
        li.style.cursor = "pointer";
        li.textContent = user.username;
        li.setAttribute("data-uid", user.uid);
        li.addEventListener("click", () => {
          currentChatContact = user;
          currentChatId = [currentUser.uid, user.uid].sort().join("_");
          chatHeaderName.textContent = user.username;
          voiceCallName.textContent = user.username;
          videoCallName.textContent = user.username;
          loadMessages();
        });
        contactsList.appendChild(li);
      });
    }
  
    // Send message
    sendBtn.addEventListener("click", () => {
      const text = messageInput.value;
      if (!text || !currentChatId) return;
      db.collection("chats").doc(currentChatId).collection("messages").add({
        senderId: currentUser.uid,
        text: text,
        timestamp: firebase.firestore.FieldValue.serverTimestamp(),
        deleted: false,
        reactions: {}
      }).then(() => {
        messageInput.value = "";
      }).catch(error => {
        console.error("Error sending message:", error);
      });
    });
  
    // Load messages with auto-scroll and toast notifications
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
            const senderName = message.senderId === currentUser.uid ? "You" : (usersMap[message.senderId] || "Unknown");
            messageElem.innerHTML = `<strong>${senderName}:</strong> ${message.text}
              <div class="mt-1 message-actions">
                <button class="deleteBtn" data-id="${doc.id}" title="Delete"><i class="bi bi-trash"></i></button>
                <button class="forwardBtn" data-id="${doc.id}" data-text="${message.text}" title="Forward"><i class="bi bi-arrow-right-square"></i></button>
                <button class="reactBtn" data-id="${doc.id}" title="React"><i class="bi bi-emoji-smile"></i></button>
                <span class="reactionDisplay">${formatReactions(message.reactions)}</span>
              </div>`;
            messagesDiv.appendChild(messageElem);
            // Show toast if browser is hidden and message is from someone else
            if (document.hidden && message.senderId !== currentUser.uid) {
              showToast(`${senderName}: ${message.text}`);
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
  
    // Show toast notifications using Bootstrap Toasts
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
          console.error("Error accessing media devices.", error);
        });
    });
  });
  