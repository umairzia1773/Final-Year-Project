document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatBody = document.getElementById('chat-body');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const newChatBtn = document.getElementById('new-chat-btn');
    const historyList = document.getElementById('history-list');
    const toggleHistoryBtn = document.getElementById('toggle-history-btn');
    const historyPanel = document.getElementById('history-panel');
    const chatArea = document.getElementById('chat-area');
    const themeToggle = document.getElementById('theme-toggle');
    const fileInput = document.getElementById('file-input');
    const attachmentBtn = document.getElementById('attachment-btn');

    // State
    let currentChatSessionId = null;
    let userId = document.body.getAttribute('data-user-id');
    let isProcessing = false;
    let darkTheme = localStorage.getItem('darkTheme') === 'true';

    // Initialize
    initializeTheme();
    loadChatSessions();
    setupEventListeners();

    // Theme initialization
    function initializeTheme() {
        if (darkTheme) {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            themeToggle.innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
        }
    }

    // Set up event listeners
    function setupEventListeners() {
        // Send message on button click
        sendButton.addEventListener('click', sendMessage);

        // Send message on Enter key (but allow Shift+Enter for new line)
        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        // Theme toggle
        themeToggle.addEventListener('click', function() {
            darkTheme = !darkTheme;
            localStorage.setItem('darkTheme', darkTheme);
            
            if (darkTheme) {
                document.documentElement.setAttribute('data-theme', 'dark');
                themeToggle.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                themeToggle.innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
            }
        });
        newChatBtn.addEventListener('click', () => {
            createNewChat().then(() => {
                // Focus on input after creating new chat
                userInput.focus();
            }).catch(error => {
                displayErrorMessage('Failed to create new chat');
            })
        });


        // Auto-resize textarea as user types
        userInput.addEventListener('input', function() {
            // Reset height to auto to get the correct scrollHeight
            this.style.height = 'auto';
            
            // Get the computed styles
            const computed = window.getComputedStyle(this);
            
            // Calculate the height including padding but not border
            const height = parseInt(computed.paddingTop) + 
                          parseInt(computed.paddingBottom) + 
                          this.scrollHeight;
            
            // Apply the height, but respect max-height from CSS
            const maxHeight = 150; // Should match CSS max-height
            this.style.height = Math.min(height, maxHeight) + 'px';
        });

        // Toggle history panel
        toggleHistoryBtn.addEventListener('click', () => {
            historyPanel.classList.toggle('hidden');
        });

        // Profile dropdown
        const profileBtn = document.getElementById('profile-btn');
        const profileDropdown = document.createElement('div');
        profileDropdown.className = 'profile-dropdown';
        profileDropdown.style.display = 'none';

        // Get user email from data attribute
        const userEmail = document.body.getAttribute('data-user-email') || 'User';

        profileDropdown.innerHTML = `
            <div class="profile-info">
                <i class="fas fa-user-circle"></i>
                <span>${userEmail}</span>
            </div>
            <div class="dropdown-divider"></div>
            <a href="/settings" class="dropdown-item"><i class="fas fa-cog"></i> Settings</a>
            <a href="/logout" class="dropdown-item"><i class="fas fa-sign-out-alt"></i> Logout</a>
        `;

        document.body.appendChild(profileDropdown);

        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const rect = profileBtn.getBoundingClientRect();
            profileDropdown.style.top = `${rect.bottom + 5}px`;
            profileDropdown.style.right = '10px';
            profileDropdown.style.display = profileDropdown.style.display === 'none' ? 'block' : 'none';
        });

        document.addEventListener('click', (e) => {
            if (!profileDropdown.contains(e.target) && e.target !== profileBtn) {
                profileDropdown.style.display = 'none';
            }
        });


        // Toggle theme
        themeToggle.addEventListener('click', function() {
            darkTheme = !darkTheme;
            localStorage.setItem('darkTheme', darkTheme);

            if (darkTheme) {
                document.documentElement.setAttribute('data-theme', 'dark');
                themeToggle.innerHTML = '<i class="fas fa-sun"></i> Light Theme';
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                themeToggle.innerHTML = '<i class="fas fa-moon"></i> Dark Theme';
            }
        });

        // Create new chat
        newChatBtn.addEventListener('click', function() {
            createNewChat();
        });

        // File upload button click
        attachmentBtn.addEventListener('click', function() {
            fileInput.click();
        });

        // File selected handler
        fileInput.addEventListener('change', handleFileUpload);
    }

    // Load chat sessions from the server
    function loadChatSessions() {
        fetch('/get_user_chat_sessions')
            .then(response => response.json())
            .then(data => {
                historyList.innerHTML = '';

                if (data.length === 0) {
                    // No chat sessions, create a welcome screen
                    displayWelcomeScreen();
                    return;
                }

                // Populate history list
                data.forEach(session => {
                    const li = document.createElement('li');
                    li.className = 'chat-session-item';
                    li.setAttribute('data-chat-id', session.session_id);

                    // Truncate session name if too long
                    let sessionName = session.session_name;
                    if (sessionName.length > 25) {
                        sessionName = sessionName.substring(0, 25) + '...';
                    }

                    li.innerHTML = `
                        <div class="chat-session-title">
                            <i class="fas fa-comments"></i>
                            <span class="session-name">${sessionName}</span>
                        </div>
                        <div class="chat-session-menu">
                            <button class="menu-btn" title="More options">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <div class="session-menu-dropdown">
                                <div class="session-menu-item rename-btn">
                                    <i class="fas fa-edit"></i>Rename
                                </div>
                                <div class="session-menu-item delete-btn">
                                    <i class="fas fa-trash"></i>Delete
                                </div>
                            </div>
                        </div>`;

                    const menuBtn = li.querySelector('.menu-btn');
                    const menuDropdown = li.querySelector('.session-menu-dropdown');
                    const renameBtn = li.querySelector('.rename-btn');
                    const deleteBtn = li.querySelector('.delete-btn');
                    const sessionNameSpan = li.querySelector('.session-name');

                    menuBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        menuDropdown.classList.toggle('show');
                    });

                    // Close dropdown when clicking outside
                    document.addEventListener('click', (e) => {
                        if (!menuBtn.contains(e.target)) {
                            menuDropdown.classList.remove('show');
                        }
                    });

                    renameBtn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        const newName = prompt('Enter new name for chat:', sessionName);
                        if (newName) {
                            try {
                                const response = await fetch('/rename_chat', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        session_id: session.session_id,
                                        new_name: newName
                                    })
                                });
                                if (response.ok) {
                                    sessionNameSpan.textContent = newName;
                                }
                            } catch (error) {
                                console.error('Error renaming chat:', error);
                            }
                        }
                        menuDropdown.classList.remove('show');
                    });

                    deleteBtn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (confirm('Are you sure you want to delete this chat?')) {
                            try {
                                const response = await fetch('/delete_chat', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        session_id: session.session_id
                                    })
                                });
                                if (response.ok) {
                                    li.remove();
                                    if (currentChatSessionId === session.session_id) {
                                        chatBody.innerHTML = '';
                                        currentChatSessionId = null;
                                        displayWelcomeScreen();
                                    }
                                }
                            } catch (error) {
                                console.error('Error deleting chat:', error);
                            }
                        }
                        menuDropdown.classList.remove('show');
                    });

                    li.addEventListener('click', function() {
                        // Highlight active session
                        document.querySelectorAll('.chat-session-item').forEach(item => {
                            item.classList.remove('active');
                        });
                        this.classList.add('active');

                        // Load chat messages for this session
                        const sessionId = this.getAttribute('data-chat-id');
                        loadChatHistory(sessionId);
                    });

                    historyList.appendChild(li);
                });

                // Load the most recent chat by default
                if (data.length > 0) {
                    const mostRecentSession = data[0];
                    currentChatSessionId = mostRecentSession.session_id;
                    loadChatHistory(currentChatSessionId);

                    // Highlight the most recent session in the list
                    const firstSessionItem = historyList.querySelector('.chat-session-item');
                    if (firstSessionItem) {
                        firstSessionItem.classList.add('active');
                    }
                }
            })
            .catch(error => {
                console.error('Error loading chat sessions:', error);
            });
    }

    // Load chat history for a specific session
    function loadChatHistory(sessionId) {
        currentChatSessionId = sessionId;
        
        // Clear existing messages before loading new ones
        chatBody.innerHTML = '';
        
        fetch(`/get_chat_history?session_id=${sessionId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received chat history:', data);

                if (!Array.isArray(data)) {
                    console.error('Expected array of messages, got:', typeof data);
                    return;
                }

                // Sort messages by timestamp to ensure correct order
                data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

                // Keep track of displayed messages to prevent duplicates
                const displayedMessages = new Set();

                data.forEach((message, index) => {
                    // Create a unique key for each message
                    const messageKey = `${message.timestamp}-${message.sender}-${message.message}`;
                    
                    if (displayedMessages.has(messageKey)) {
                        console.log(`Skipping duplicate message: ${messageKey}`);
                        return;
                    }

                    if (!message || typeof message !== 'object') {
                        console.error(`Invalid message at index ${index}:`, message);
                        return;
                    }

                    if (!message.message || !message.sender) {
                        console.error(`Missing required message properties:`, message);
                        return;
                    }

                    // Display the message
                    displayMessage(
                        message.message,
                        message.sender,
                        message.timestamp
                    );

                    // Mark this message as displayed
                    displayedMessages.add(messageKey);
                });

                scrollToBottom();
            })
            .catch(error => {
                console.error('Error loading chat history:', error);
                displayErrorMessage('Failed to load chat history. Please try again.');
            });
    }

    function displayMessage(content, sender, timestamp) {
        // Create message container
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;

        // Safely format the timestamp
        let formattedTime;
        try {
            // Try to parse the timestamp
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                // If invalid date, use current time
                formattedTime = new Date().toLocaleString();
                console.warn('Invalid timestamp received:', timestamp);
            } else {
                formattedTime = date.toLocaleString();
            }
        } catch (error) {
            console.error('Error formatting timestamp:', error);
            formattedTime = new Date().toLocaleString();
        }

        // Create message content with proper styling
        const messageContent = document.createElement('div');
        messageContent.className = `message-content ${sender}`;

        try {
            // Always use markdown for both bot and user messages
            const markdownContent = marked.parse(content);
            
            messageContent.innerHTML = `
                <div class="markdown-content">${markdownContent}</div>
                <small class="timestamp">${formattedTime}</small>
            `;
        } catch (error) {
            console.error('Error parsing markdown:', error);
            // Fallback to plain text if markdown parsing fails
            messageContent.innerHTML = `
                <div class="markdown-content"><p>${content}</p></div>
                <small class="timestamp">${formattedTime}</small>
            `;
        }

        // Add message to chat
        messageDiv.appendChild(messageContent);
        chatBody.appendChild(messageDiv);
        
        // Highlight any code blocks
        messageDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }


    // function displayMessage(content, sender, timestamp) {
    //     const messageDiv = document.createElement('div');
    //     messageDiv.className = `chat-message ${sender}-message`;

    //     // Convert timestamp to a more readable format
    //     const formattedTime = new Date(timestamp).toLocaleString();

    //     // Different styling for user and bot messages
    //     if (sender === 'bot') {
    //         messageDiv.innerHTML = `
    //             <div class="message-content bot">
    //                 <div class="markdown-content">${content}</div>
    //                 <small class="timestamp">${formattedTime}</small>
    //             </div>
    //         `;
    //     } else {
    //         messageDiv.innerHTML = `
    //             <div class="message-content user">
    //                 <p>${content}</p>
    //                 <small class="timestamp">${formattedTime}</small>
    //             </div>
    //         `;
    //     }

    //     chatBody.appendChild(messageDiv);
    // }

    // Display welcome screen for new users
    function displayWelcomeScreen() {
        chatBody.innerHTML = `
            <div class="welcome-container">
                <h1 class="welcome-title">AI Assistant</h1>
                <p class="welcome-subtitle">Ask me anything about code, concepts, or general knowledge</p>
                <div class="suggestions">
                    <div class="suggestion" onclick="document.getElementById('user-input').value = 'Explain the concept of machine learning in simple terms'; document.getElementById('user-input').focus();">
                        <p>"Explain the concept of machine learning in simple terms"</p>
                    </div>
                    <div class="suggestion" onclick="document.getElementById('user-input').value = 'Write a Python function that checks if a string is a palindrome'; document.getElementById('user-input').focus();">
                        <p>"Write a Python function that checks if a string is a palindrome"</p>
                    </div>
                    <div class="suggestion" onclick="document.getElementById('user-input').value = 'How do I optimize the performance of a web application?'; document.getElementById('user-input').focus();">
                        <p>"How do I optimize the performance of a web application?"</p>
                    </div>
                    <div class="suggestion" onclick="document.getElementById('user-input').value = 'Create a simple CSS animation for a button hover effect'; document.getElementById('user-input').focus();">
                        <p>"Create a simple CSS animation for a button hover effect"</p>
                    </div>
                </div>
                <p class="disclaimer">AI responses may not always be accurate. Verify important information.</p>
            </div>
        `;
    }

    // Create a new chat session
    function createNewChat() {
        return new Promise((resolve, reject) => {
            fetch('/start_new_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                    reject(data.error);
                    return;
                }
                
                // Clear chat area and show welcome screen
                chatBody.innerHTML = '';
                displayWelcomeScreen();

                // Update current session
                currentChatSessionId = data.session_id;

                // Refresh sessions list
                loadChatSessions();
                
                resolve(data.session_id);
            })
            .catch(error => {
                console.error('Error creating new chat:', error);
                reject(error);
            });
        });
    }


    function sendMessage() {
        const message = userInput.value.trim();

        if (!message || isProcessing) {
            return;
        }

        const sendMessageAction = function() {
            isProcessing = true;

            // Get current timestamp in ISO format
            const currentTime = new Date().toISOString();
            
            // Display user message immediately
            displayMessage(message, 'user', currentTime);

            // Clear input and adjust UI
            userInput.value = '';
            userInput.style.height = 'auto';
            appendLoadingIndicator();
            scrollToBottom();

            // Store message in database
            fetch('/store_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: currentChatSessionId,
                    user_id: userId,
                    message: message,
                    sender: 'user',
                    timestamp: currentTime,
                    is_first_message: !document.querySelector('.chat-message') // Check if this is first message
                }),
            })
            .then(response => response.json())
            .then(() => {
                // Send to backend for AI processing
                return fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: message
                    }),
                });
            })
            .then(response => response.json())
            .then(data => {
                removeLoadingIndicator();
                
                if (data.error) {
                    displayErrorMessage(data.error);
                    return;
                }

                // Get bot response from the correct field
                const botResponse = data.answer || data.response;
                if (!botResponse) {
                    console.error('No response from bot:', data);
                    displayErrorMessage('Received empty response from bot');
                    return;
                }

                // Store bot response
                const botResponseTime = new Date().toISOString();
                return fetch('/store_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: currentChatSessionId,
                        user_id: userId,
                        message: botResponse,
                        sender: 'bot',
                        timestamp: botResponseTime
                    }),
                })
                .then(response => response.json())
                .then(() => {
                    // Display bot message after storing
                    displayMessage(botResponse, 'bot', botResponseTime);
                    scrollToBottom();
                    
                    // Refresh chat sessions to update titles
                    loadChatSessions();
                });
            })
            .catch(error => {
                console.error('Error:', error);
                removeLoadingIndicator();
                displayErrorMessage('An error occurred while processing your message');
            })
            .finally(() => {
                isProcessing = false;
            });
        };

        if (!currentChatSessionId) {
            createNewChat().then(() => {
                sendMessageAction();
            });
        } else {
            sendMessageAction();
        }
    }

    function formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                throw new Error('Invalid date');
            }
            
            // Always show in format "Mar 16, 1:04 AM"
            const formatted = date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            }).replace(',', '');
            
            return formatted;
        } catch (error) {
            console.error('Error formatting timestamp:', error, 'for timestamp:', timestamp);
            // Return current time in same format if there's an error
            return new Date().toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            }).replace(',', '');
        }
    }

    function displayMessage(content, sender, timestamp) {
        // Create message container
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;

        // Format the timestamp consistently
        const formattedTime = formatTimestamp(timestamp);

        // Create message content with proper styling
        const messageContent = document.createElement('div');
        messageContent.className = `message-content ${sender}`;

        try {
            // Always use markdown for both bot and user messages
            const markdownContent = marked.parse(content || '');
            
            messageContent.innerHTML = `
                <div class="markdown-content">${markdownContent}</div>
                <small class="timestamp">${formattedTime}</small>
            `;
        } catch (error) {
            console.error('Error parsing markdown:', error);
            // Fallback to plain text if markdown parsing fails
            messageContent.innerHTML = `
                <div class="markdown-content"><p>${content || ''}</p></div>
                <small class="timestamp">${formattedTime}</small>
            `;
        }

        // Add message to chat
        messageDiv.appendChild(messageContent);
        chatBody.appendChild(messageDiv);
        
        // Highlight any code blocks
        messageDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    // Append loading indicator
    function appendLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message bot-message loading-message';
        loadingDiv.innerHTML = `
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        chatBody.appendChild(loadingDiv);
    }

    // Remove loading indicator
    function removeLoadingIndicator() {
        const loadingMessage = document.querySelector('.loading-message');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }

    // Display error message
    function displayErrorMessage() {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chat-message bot-message';
        errorDiv.innerHTML = `
            <p>Sorry, I encountered an error processing your request. Please try again.</p>
            <small>${new Date().toLocaleTimeString()}</small>
        `;
        chatBody.appendChild(errorDiv);
    }

    // Handle file upload
    function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        // Show uploading message
        const uploadingDiv = document.createElement('div');
        uploadingDiv.className = 'chat-message user-message';
        uploadingDiv.innerHTML = `
            <p>Uploading file: ${file.name}...</p>
            <small>${new Date().toLocaleTimeString()}</small>
        `;
        chatBody.appendChild(uploadingDiv);
        scrollToBottom();

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    uploadingDiv.innerHTML = `
                        <p>Error uploading file: ${data.error}</p>
                        <small>${new Date().toLocaleTimeString()}</small>
                    `;
                } else {
                    uploadingDiv.innerHTML = `
                        <p>Uploaded file: ${file.name}</p>
                        <small>${new Date().toLocaleTimeString()}</small>
                    `;

                    // Display assistant message about the file
                    const responseDiv = document.createElement('div');
                    responseDiv.className = 'chat-message bot-message';
                    responseDiv.innerHTML = `
                        <div class="markdown-content">
                            <p>I've processed your file: <strong>${file.name}</strong>. You can now ask me questions about it.</p>
                        </div>
                        <small>${new Date().toLocaleTimeString()}</small>
                    `;
                    chatBody.appendChild(responseDiv);
                }

                // Reset file input
                fileInput.value = "";
                scrollToBottom();
            })
            .catch(error => {
                console.error('Error uploading file:', error);
                uploadingDiv.innerHTML = `
                    <p>Error uploading file: Network error</p>
                    <small>${new Date().toLocaleTimeString()}</small>
                `;
                fileInput.value = "";
                scrollToBottom();
            });
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatBody.scrollTop = chatBody.scrollHeight;
    }
});