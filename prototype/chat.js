// Wait for the DOM to fully load before adding event listeners
document.addEventListener("DOMContentLoaded", () => {
    // Select the input field and send button
    const userInput = document.querySelector("#user-input");  // Updated selector to match HTML
    const sendButton = document.querySelector("#send-button");
    const chatBody = document.querySelector("#chat-body");

    // Function to append the message to the chat body
    const appendMessage = (message, isBot = false) => {
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", isBot ? "bot-message" : "user-message");
        messageElement.innerHTML = `<p>${message}</p>`;
        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;  // Scroll to the bottom of the chat
    };

    // Function to handle sending a message
    const sendMessage = () => {
        const userMessage = userInput.value.trim();

        if (userMessage === "") {
            appendMessage("Please enter a question.", true);
            return;
        }

        // Append user message to the chat
        appendMessage(userMessage, false);
        userInput.value = "";  // Clear the input field


        const isURL = userMessage.startsWith("http");
        const endpoint = isURL ? "/scrape" : "/ask";
        const payload = isURL ? { url: userMessage } : { question: userMessage };
        fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    appendMessage(`Error: ${data.error}`, true);
                } else if (data.answer) {
                    appendMessage(data.answer, true);
                } else {
                    appendMessage(JSON.stringify(data), true);
                }
            })
            .catch(() => {
                appendMessage("Something went wrong. Please try again later.", true);
            });
        };
            sendButton.addEventListener("click", sendMessage);

            userInput.addEventListener("keypress", (event) => {
                if (event.key === "Enter") {
                    sendMessage();
                }
            });
        });
        // Send the question to the Flask backend
        fetch("http://127.0.0.1:5000/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: userMessage }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.answer) {
                    appendMessage(data.answer, true); // Display bot message
                } else {
                    appendMessage("Something went wrong. Please try again later.", true);
                }
            })
            .catch(() => {
                appendMessage("Something went wrong. Please try again later.", true);
            });
            // };

    // Add click event listener to the send button
    sendButton.addEventListener("click", sendMessage);

    // Allow pressing Enter to send a message
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
// });

document.getElementById("send-button").addEventListener("click", function() {
    let userInput = document.getElementById("user-input").value.trim();
    if (userInput === "") return;

    // Display user message immediately
    displayMessage(userInput, "user");

    fetch("/send_message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => response.json())
    .then(data => {
        if (data.bot_message) {
            displayMessage(data.bot_message, "bot"); // Display bot response
        } else if (data.error) {
            alert("Error: " + data.error);
        }
    })
    .catch(error => console.error("Error sending message:", error));

    // Clear input field
    document.getElementById("user-input").value = "";
});

function displayMessage(message, sender) {
    let chatBody = document.getElementById("chat-body");
    let messageDiv = document.createElement("div");
    messageDiv.classList.add("chat-message");
    messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");
    messageDiv.innerHTML = `<p>${message}</p>`;
    chatBody.appendChild(messageDiv);
}

function sendMessage() {
    let message = document.getElementById("message_input").value.trim();
    if (!message) return;

    fetch("/send_message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.session_id) {
            updateChatHistory(data.session_id, message);
        }
    })
    .catch(error => console.error("Error sending message:", error));
}

function updateChatHistory(sessionId, message) {
    let sessionName = message.split(" ").slice(0, 5).join(" "); // Get first 5 words
    let chatList = document.getElementById("chat_history");

    // Remove if session already exists (avoids duplicates)
    document.querySelector(`#session-${sessionId}`)?.remove();

    let newChatItem = document.createElement("li");
    newChatItem.id = `session-${sessionId}`;
    newChatItem.innerHTML = `<a href="#" onclick="loadChat(${sessionId})">${sessionName}</a>`;
    
    // Insert new session at the top
    chatList.prepend(newChatItem);
}

function loadChatHistory() {
    fetch('/get_chat_history')
    .then(response => response.json())
    .then(data => {
        let chatBody = document.getElementById("chat-body");
        chatBody.innerHTML = ""; // Clear old messages

        data.forEach(msg => {
            let messageDiv = document.createElement("div");
            messageDiv.classList.add("chat-message");
            if (msg.sender === "user") {
                messageDiv.classList.add("user-message");
            } else {
                messageDiv.classList.add("bot-message");
            }
            messageDiv.innerHTML = `<p>${msg.message}</p><small>${msg.timestamp}</small>`;
            chatBody.appendChild(messageDiv);
        });
    })
    .catch(error => console.error("Error fetching chat history:", error));
}

// Call the function when the page loads
window.onload = loadChatHistory;
