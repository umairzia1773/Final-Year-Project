
document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.querySelector("#user-input");
    const sendButton = document.querySelector("#send-button");
    const chatBody = document.querySelector("#chat-body");
    const historyList = document.querySelector("#history-list");
    const toggleHistoryBtn = document.querySelector("#toggle-history-btn");
    const fileInput = document.querySelector("#file-input");
    const attachmentBtn = document.querySelector("#attachment-btn");
    const chatArea = document.getElementById("chat-area");
    let sessionId = null;

    fetchUserChatSessions();
    function fetchUserChatSessions() {
        fetch("/get_user_chat_sessions")
            .then(response => response.json())
            .then(data => {
                
                if (data.error) {
                    console.error("Error fetching chat sessions:", data.error);
                    return;
                }
                data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                updateChatHistoryPanel(data);
                    
                const latestSession = JSON.parse(sessionStorage.getItem("latest_chat_session"));
                if (latestSession) {
                    addNewChatSession(latestSession);
                    sessionStorage.removeItem("latest_chat_session"); // Remove to prevent duplication
                }
            })
            .catch(error => console.error("Error fetching chat sessions:", error));
    }
    
    function updateChatHistoryPanel(chatSessions) {
        const historyList = document.getElementById("history-list");
        const currentSessionId = sessionStorage.getItem("chat_session_id");
        historyList.innerHTML = ""; // Clear existing items
    
        chatSessions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); // Ensure sorting latest first
        chatSessions.forEach(session => {
                const historyItem = document.createElement("li");
                historyItem.textContent = session.session_name.length > 40 
                    ? session.session_name.slice(0, 40) + "..." 
                    : session.session_name; // Trim to 40 characters
    
                historyItem.classList.add("history-item");
                historyItem.dataset.chatId = session.session_id; // Ensure correct ID is assigned
    
                // Load chat history when clicked
                historyItem.onclick = function () {
                    if (session.session_id) {
                        loadChatHistory(session.session_id);
                    } else {
                        console.error("Chat session ID missing for this history item:", session);
                    }
                };
                
                
                
                
                historyList.appendChild(historyItem);  // ✅ Inserts at the top

            });
    }
    
    function addNewChatSession(session) {
        const historyList = document.getElementById("history-list");
        
        let existingItem = document.querySelector(`[data-chat-id="${session.session_id}"]`);
        if (existingItem) return;

        const historyItem = document.createElement("li");
        historyItem.textContent = session.session_name.length > 40 
        ? session.session_name.slice(0, 40) + "..." 
        : session.session_name;
    
        historyItem.classList.add("history-item");
        // historyItem.dataset.chatId = session.chat_session_id;
        historyItem.dataset.chatId = session.session_id;

        
        // historyItem.onclick = function () {
        //     if (session.chat_session_id) {
        //         loadChatHistory(session.chat_session_id);
        //     } else {
        //         console.error("Chat session ID missing for this history item:", session);
        //     }
        // };
        historyItem.onclick = function () {
            if (session.session_id) {
                loadChatHistory(session.session_id);
            } else {
                console.error("Chat session ID missing for this history item:", session);
            }
        };
        
        
    
        // historyList.prepend(historyItem); // ✅ Only for new chat sessions
        historyList.prepend(historyItem);
        sessionStorage.setItem("latest_chat_session", JSON.stringify(session));
        // fetchUserChatSessions();
        // sessionStorage.setItem("latest_chat_session", JSON.stringify(session));
    }
    
    function displayChatMessages(messages) {
        const chatWindow = document.getElementById("chat-window");
        chatWindow.innerHTML = ""; // Clear previous messages
    
        messages.forEach(msg => { // Append messages in correct order (old to new)
            chatWindow.appendChild(createMessageElement(msg));
        });
    
        // Auto-scroll to the latest message
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
    
    // Function to create a message element
    function createMessageElement(msg) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message");
    
        if (msg.sender === "user") {
            messageElement.classList.add("user-message");
        } else {
            messageElement.classList.add("bot-message");
        }
    
        const messageText = document.createElement("p");
        messageText.textContent = msg.message; // Assuming msg.message contains the text
    
        messageElement.appendChild(messageText);
        return messageElement;
    }
    
    function loadChatHistory(sessionId) {
        if (!sessionId || sessionId === "undefined") {
            console.error("Invalid session ID:", sessionId);
            return;
        }
        sessionStorage.setItem("chat_session_id", sessionId);
        fetch(`/get_chat_history?session_id=${sessionId}`)
            .then(response => response.json())
            .then(data => {
                if (!Array.isArray(data)) {
                    console.error("Invalid chat history format received:", data);
                    return;
                }
    
                const chatBox = document.getElementById("chat-body");
                chatBox.innerHTML = ""; // Clear existing messages
    
                data.forEach(message => {
                    appendMessage(message.message, message.sender );
                });
    
                console.log(`Chat history loaded for session: ${sessionId}`); // Set current session
            })
            .catch(error => console.error("Error fetching chat history:", error));
    }
    
    document.getElementById("send-button").addEventListener("click", () => {
        const userInput = document.getElementById("user-input").value.trim();
        if (!userInput) return; // Don't send empty messages
    
        let sessionId = sessionStorage.getItem("chat_session_id");
    
        fetch("/send_message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                user_id: userId, 
                session_id: sessionId, 
                message: userInput 
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.chat_session_id) {
                const isNewSession = !sessionId || data.is_new_session;
                
                // ✅ Update session storage if a new session was created
                if (isNewSession) {
                    sessionId = data.chat_session_id;
                    sessionStorage.setItem("chat_session_id", sessionId);
                }
    
                // ✅ Append user message to chat body
                const chatBody = document.getElementById("chat-body");
                const userMessageDiv = document.createElement("div");
                userMessageDiv.classList.add("chat-message", "user-message");
                userMessageDiv.innerHTML = `<p>${userInput}</p><small>Just now</small>`;
                chatBody.appendChild(userMessageDiv);
    
                // ✅ Ensure new session appears at the **top** when created
                const historyList = document.getElementById("history-list");
                let existingSession = document.querySelector(`[data-chat-id="${sessionId}"]`);
                
                if (isNewSession) {
                    if (!existingSession) {
                        const historyItem = document.createElement("li");
                        historyItem.textContent = userInput.substring(0, 20); // First few words as title
                        historyItem.classList.add("chat-session-item");
                        historyItem.dataset.chatId = sessionId;
                        historyItem.addEventListener("click", () => loadChatHistory(sessionId));
    
                        // ✅ Always insert at the **top**
                        historyList.prepend(historyItem);
                    } else {
                        // ✅ Move existing session to the top
                        historyList.prepend(existingSession);
                    }
                }
    
                // ✅ Clear input field after sending message
                document.getElementById("user-input").value = "";
            }
        })
        .catch(error => console.error("Error sending message:", error));
    });
    
    
    
    // 🔥 Function to make sure history list is sorted (most recent session first)
    function reorderChatHistory() {
        const historyList = document.getElementById("history-list");
        const items = Array.from(historyList.children);
        
        // Sort sessions by newest first
        items.sort((a, b) => {
            return b.dataset.chatId - a.dataset.chatId;
        });
    
        // Clear and re-add sorted items
        historyList.innerHTML = "";
        items.forEach(item => historyList.appendChild(item));
    }
    
        
    
    document.getElementById("new-chat-btn").addEventListener("click", () => {
        fetch("/start_new_chat", { 
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.session_id) {
                sessionId = data.session_id;
                sessionStorage.setItem("chat_session_id", sessionId);
    
                chatBody.innerHTML = "";
    
                const historyItem = document.createElement("li");
                historyItem.textContent = "New Chat Session";
                historyItem.classList.add("history-item");
                historyItem.dataset.chatId = sessionId;
                historyItem.addEventListener("click", () => loadChatHistory(sessionId));
    
                // **Insert at the top instead of appending at the bottom**
                historyList.prepend(historyItem);  // <=== This line fixes your issue
            }
        })
        .catch(error => console.error("Error starting new chat session:", error));
    });
    
    
    // let sessionId = sessionStorage.getItem("chat_session_id");
    // if (!sessionId) {
    //     fetch("/start_new_chat", { 
    //         method: "POST",
    //         headers: { "Content-Type": "application/json" },
    //         body: JSON.stringify({ user_id: userId })
    //     })
    //     .then(response => response.json())
    //     .then(data => {
    //         if (data.session_id) {
    //             sessionId = data.session_id;
    //             sessionStorage.setItem("chat_session_id", sessionId);
    //         }
    //     })
    //     .catch(error => console.error("Error starting chat session:", error));
    // } else {
    //     loadChatHistory(sessionId);
    // }


    toggleHistoryBtn.addEventListener("click", () => {
        document.getElementById("history-panel").classList.toggle("d-none");
    });

    const appendMessage = (message, sender = "bot") => {
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", sender === "user" ? "user-message" : "bot-message");
        messageElement.innerHTML = `<p>${message}</p>`;
        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;
    };

    const sendMessageHandler = () => {
        const userMessage = userInput.value.trim();
        if (!userMessage) return;
        
        appendMessage(userMessage, "user");
        userInput.value = "";
        if (!sessionId) {
            fetch("/start_new_chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.session_id) {
                    sessionId = data.session_id; // Store new session ID
                    sessionStorage.setItem("chat_session_id", sessionId);
    
                    // Add new session to history panel at the top
                    // addNewChatSession(sessionId, userMessage.slice(0, 20) + "...");
                    const newSession = {
                        session_id: sessionId,
                        session_name: userMessage.substring(0, 20) + "..."
                    };
                    addNewChatSession(newSession);
                    // Now send the message
                    sendQuestionToBackend(userMessage);
                }
            })
            .catch(error => console.error("Error creating new session:", error));
        } else {
            sendQuestionToBackend(userMessage);
        }
    };
        
        

    
    const sendQuestionToBackend = (userMessage) => {
        fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: userMessage, session_id: sessionId })  
        })
        .then(response => response.json())
        .then(data => {
            if (data.answer) {
                appendMessage(data.answer, "bot");

                const historyItem = document.querySelector(`[data-chat-id="${sessionId}"]`);
                if (!historyItem) {
                    const newHistoryItem = document.createElement("li");
                    newHistoryItem.textContent = userMessage.slice(0, 20) + "...";
                    newHistoryItem.classList.add("history-item");
                    newHistoryItem.dataset.chatId = sessionId;
                    newHistoryItem.addEventListener("click", () => loadChatHistory(sessionId));
                    historyList.appendChild(newHistoryItem);
                } else if (historyItem.textContent === "New Chat Session") {
                    historyItem.textContent = userMessage.slice(0, 20) + "...";
                }
            }
        })
        .catch(error => console.error("Error sending message:", error));
        
    };
    sendButton.addEventListener("click", sendMessageHandler);
        userInput.addEventListener("keypress", (event) => {
            if (event.key === "Enter") sendMessageHandler();
        });
    
    document.addEventListener("DOMContentLoaded", fetchUserChatSessions);

    attachmentBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (event) => {
        const file = event.target.files[0];
        if (file && file.type === "application/pdf") {
            const formData = new FormData();
            formData.append("file", file);
            fetch("/upload", { method: "POST", body: formData })
            .then(response => response.json())
            .then(data => console.log(data.message || data.error))
            .catch(error => console.error("Error uploading file:", error));
        } else {
            alert("Please select a PDF file.");
        }
    });
});
