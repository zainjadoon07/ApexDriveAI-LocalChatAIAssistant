// app.js - WebSocket Streaming Client with Smooth Token Rendering

let sessionId = "user_sess_" + Math.random().toString(36).substring(2, 9);
let socket = null;
let currentBotBubble = null;
let currentBotText = "";
let isStreaming = false;

const messagesContainer = document.getElementById("messages-container");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const welcomeBox = document.getElementById("welcome-box");
const newChatBtn = document.getElementById("new-chat-btn");
const headerMetrics = document.getElementById("header-metrics");

// Connect to WebSocket endpoint
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => console.log("WebSocket connected to backend");

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === "token") {
        currentBotText += data.content;
        const contentEl = currentBotBubble.querySelector(".content");
        if (contentEl) {
          const parsed = window.marked ? marked.parse(currentBotText) : currentBotText;
          contentEl.innerHTML = parsed + '<span class="streaming-cursor"></span>';
        }
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

      } else if (data.type === "end") {
        isStreaming = false;
        
        // Remove blinking cursor and finalize markdown
        if (currentBotBubble) {
          const contentEl = currentBotBubble.querySelector(".content");
          if (contentEl) {
            contentEl.innerHTML = window.marked ? marked.parse(currentBotText) : currentBotText;
          }

          const metricsEl = currentBotBubble.querySelector(".metrics-tag");
          if (metricsEl && data.metrics) {
            const m = data.metrics;
            metricsEl.innerHTML = `
              <span class="ttft">TTFT: ${m.ttft_ms || 0}ms</span>
              <span>Speed: ${m.tps || 0} tok/s</span>
              <span>Total: ${m.total_time_s || 0}s</span>
            `;
            const metricsText = document.getElementById("metrics-text");
            if (m.tps && metricsText) {
              metricsText.innerText = `${m.tps} tok/s`;
            }
          }
        }

        currentBotBubble = null;
        currentBotText = "";
        messageInput.focus();
      }
    } catch (err) {
      console.error("Error parsing WebSocket packet:", err);
    }
  };

  socket.onclose = () => {
    console.log("WebSocket connection closed. Retrying in 2s...");
    setTimeout(connectWebSocket, 2000);
  };
}

// Send user message
function sendMessage(text) {
  const msg = text || messageInput.value.trim();
  if (!msg || isStreaming) return;

  if (welcomeBox && welcomeBox.style.display !== "none") {
    welcomeBox.style.display = "none";
  }

  // 1. Render User Message
  appendMessageDOM("user", "U", escapeHTML(msg));

  // 2. Render Bot Placeholder for streaming
  currentBotBubble = appendMessageDOM("bot", "A", '<span class="streaming-cursor"></span>');
  currentBotText = "";
  isStreaming = true;

  // 3. Clear Input
  messageInput.value = "";

  // 4. Send via WebSocket
  socket.send(JSON.stringify({
    session_id: sessionId,
    message: msg
  }));

  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendMessageDOM(role, avatarText, initialHTML) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const userIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>`;

  const botIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 36 36" fill="none"><polygon points="18,3 33,30 3,30" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linejoin="round"/><circle cx="18" cy="18" r="3" fill="currentColor"/></svg>`;

  const avatarHTML = role === "user" ? userIcon : botIcon;

  row.innerHTML = `
    <div class="avatar">${avatarHTML}</div>
    <div class="bubble-wrap">
      <div class="bubble"><div class="content">${initialHTML}</div></div>
      <div class="metrics-tag"></div>
    </div>
  `;
  messagesContainer.appendChild(row);
  return row;
}

function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}

function sendQuickPrompt(promptText) {
  sendMessage(promptText);
}

// Event Listeners
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

newChatBtn.addEventListener("click", async () => {
  try {
    await fetch("/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId })
    });
  } catch (e) {
    console.warn("Reset failed:", e);
  }
  
  sessionId = "user_sess_" + Math.random().toString(36).substring(2, 9);
  messagesContainer.innerHTML = "";
  if (welcomeBox) {
    welcomeBox.style.display = "flex";
    messagesContainer.appendChild(welcomeBox);
  }
  if (headerMetrics) {
    const metricsText = document.getElementById("metrics-text");
    if (metricsText) metricsText.innerText = "Ready";
  }
});

// Initialize on page load
connectWebSocket();
