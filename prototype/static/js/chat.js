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
