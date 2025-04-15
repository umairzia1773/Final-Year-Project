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
    let sentMessages = new Set();
    let isWaitingForResponse = false;

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
        newChatBtn.addEventListener('click', handleNewChat);

        // Auto-resize textarea as user types
        userInput.addEventListener('input', function() {
            adjustTextAreaHeight(this);
        });
            
        userInput.addEventListener('focus', function() {
            if (this.style.height < '24px') {
                this.style.height = '24px';
            }
        });

        // Reset height on send
        sendButton.addEventListener('click', () => {
            userInput.style.height = '24px';
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

        // File upload button click
        attachmentBtn.addEventListener('click', function() {
            fileInput.click();
        });

        // File selected handler
        fileInput.addEventListener('change', handleFileUpload);

        // Add these event listeners
        userInput.addEventListener('input', function() {
            adjustTextAreaHeight(this);
        });

        userInput.addEventListener('keyup', function(e) {
            if (e.key === 'Backspace' || e.key === 'Delete') {
                adjustTextAreaHeight(this);
            }
        });

        // Reset input field
        function clearInput() {
            userInput.value = '';
            userInput.style.height = '48px';
            userInput.style.overflowY = 'hidden';
        }

        // Initialize input height when page loads
        userInput.style.height = '48px';

        // Add this to handle paste events
        userInput.addEventListener('paste', function() {
            setTimeout(() => adjustTextAreaHeight(this), 0);
        });
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
        chatBody.innerHTML = '';
        
        fetch(`/get_chat_history?session_id=${sessionId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Loaded chat history:', data); // Debug log
                
                if (data.length === 0) {
                    displayWelcomeScreen();
                    return;
                }

                // Sort messages by timestamp
                data.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

                data.forEach(message => {
                    const messageContent = message.message;
                    const sender = message.sender;
                    const timestamp = message.created_at;
                    
                    displayMessage(messageContent, sender, timestamp);
                });

                scrollToBottom();
            })
            .catch(error => {
                console.error('Error loading chat history:', error);
                displayErrorMessage('Failed to load chat history');
            });
    }

    function displayMessage(content, sender, timestamp) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;

        if (sender === 'bot' && !content) {
            // Loading indicator for bot
            messageDiv.innerHTML = `
                <div class="loading-indicator">
                    <div class="loading-dots">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                </div>
            `;
        } else {
        try {
            const markdownContent = marked.parse(content || '');
                messageDiv.innerHTML = `
                <div class="markdown-content">${markdownContent}</div>
                    <div class="message-timestamp">${formatTimestamp(timestamp)}</div>
            `;
        } catch (error) {
                console.error('Markdown parsing error:', error);
            messageDiv.innerHTML = `
                <div class="markdown-content"><p>${content || ''}</p></div>
                <div class="message-timestamp">${formatTimestamp(timestamp)}</div>
            `;
            }
        }

        chatBody.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }

    // Display welcome screen for new users
    function displayWelcomeScreen() {
        chatBody.innerHTML = `
            <div class="welcome-container">
                <h1 class="welcome-title">AI Assistant</h1>
                <p class="welcome-subtitle">Ask me anything about code, concepts, or general knowledge</p>
                <div class="suggestions">
                    <div class="suggestion" onclick="setInput('Explain the concept of machine learning in simple terms')">
                        <p>"Explain the concept of machine learning in simple terms"</p>
                    </div>
                    <div class="suggestion" onclick="setInput('Write a Python function that checks if a string is a palindrome')">
                        <p>"Write a Python function that checks if a string is a palindrome"</p>
                    </div>
                    <div class="suggestion" onclick="setInput('How do I optimize the performance of a web application?')">
                        <p>"How do I optimize the performance of a web application?"</p>
                    </div>
                    <div class="suggestion" onclick="setInput('Create a simple CSS animation for a button hover effect')">
                        <p>"Create a simple CSS animation for a button hover effect"</p>
                    </div>
                </div>
                
            </div>
        `;
    }

    function setInput(text) {
        userInput.value = text;
        adjustTextAreaHeight(userInput);
        userInput.focus();
    }

    // Create a new chat session
    async function createNewChat(initialMessage = '') {
        try {
            // Create session first
            const response = await fetch('/start_new_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    initial_message: initialMessage
                }),
            });
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            
            currentChatSessionId = data.session_id;
            
            // Get first few words for session name
            let sessionName = initialMessage
                .split(' ')
                .slice(0, 4)
                .join(' ');
            sessionName = sessionName.length > 30 ? 
                sessionName.substring(0, 27) + '...' : 
                sessionName;

            // Update session name
            await fetch('/rename_chat_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: currentChatSessionId,
                    new_name: sessionName
                })
            });
            
            // Update sidebar immediately
            const historyList = document.getElementById('history-list');
            const newSessionElement = document.createElement('li');
            newSessionElement.className = 'chat-session-item active';
            newSessionElement.setAttribute('data-chat-id', currentChatSessionId);
            newSessionElement.innerHTML = `
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

            // Remove active class from other sessions
            document.querySelectorAll('.chat-session-item').forEach(item => {
                item.classList.remove('active');
            });

            // Add new session to top of list
            if (historyList.firstChild) {
                historyList.insertBefore(newSessionElement, historyList.firstChild);
            } else {
                historyList.appendChild(newSessionElement);
            }

            // Add event listeners to new session
            setupSessionEventListeners(newSessionElement);
            
            return data;
        } catch (error) {
            console.error('Error creating new chat:', error);
            throw error;
        }
    }

    // Add this helper function to setup session event listeners
    function setupSessionEventListeners(sessionElement) {
        const menuBtn = sessionElement.querySelector('.menu-btn');
        const menuDropdown = sessionElement.querySelector('.session-menu-dropdown');
        const renameBtn = sessionElement.querySelector('.rename-btn');
        const deleteBtn = sessionElement.querySelector('.delete-btn');

        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menuDropdown.classList.toggle('show');
        });

        renameBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const sessionId = sessionElement.getAttribute('data-chat-id');
            const nameSpan = sessionElement.querySelector('.session-name');
            makeSessionNameEditable(sessionElement, sessionId);
            menuDropdown.classList.remove('show');
        });

        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const sessionId = sessionElement.getAttribute('data-chat-id');
            handleDeleteSession(sessionId, sessionElement);
            menuDropdown.classList.remove('show');
        });

        sessionElement.addEventListener('click', () => {
            const sessionId = sessionElement.getAttribute('data-chat-id');
            loadChatHistory(sessionId);
            
            // Update active state
            document.querySelectorAll('.chat-session-item').forEach(item => {
                item.classList.remove('active');
            });
            sessionElement.classList.add('active');
        });
    }

    async function handleNewChat() {
        if (isProcessing) return;
        
        try {
            // Clear current chat area
            chatBody.innerHTML = '';
            
            // Display welcome screen
            displayWelcomeScreen();
            
            // Reset current session ID
            currentChatSessionId = null;
            
            // Remove active class from all sessions
            document.querySelectorAll('.chat-session-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Clear input
            clearInput();
            
            // Focus on input
            userInput.focus();
            
        } catch (error) {
            console.error('Error creating new chat:', error);
            displayErrorMessage('Failed to create new chat');
        }
    }

    // Update event listener for new chat button
    document.getElementById('new-chat-btn').addEventListener('click', handleNewChat);

    // Update sendMessage function to handle first message in new chat
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message || isProcessing) return;
        
        isProcessing = true;

        try {
            // Remove welcome screen if it exists
            const welcomeContainer = document.querySelector('.welcome-container');
            if (welcomeContainer) {
                welcomeContainer.remove();
            }

            // Create new session if needed
            if (!currentChatSessionId) {
                try {
                    const data = await createNewChat(message);
                    currentChatSessionId = data.session_id;
                    
                    // Remove active class from all sessions
                    document.querySelectorAll('.chat-session-item').forEach(item => {
                        item.classList.remove('active');
                    });
                } catch (error) {
                    console.error('Error creating new session:', error);
                    displayErrorMessage('Failed to create new chat session');
                    isProcessing = false;
                    return;
                }
            }

            // Display user message
            displayMessage(message, 'user', new Date().toISOString());
            
            // Clear and reset input
            clearInput();

            // Show loading indicator
            const loadingElement = displayMessage('', 'bot', new Date().toISOString());

            // Send message to backend
            const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                    'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                    message: message,
                    session_id: currentChatSessionId
                })
            });

            const data = await response.json();
            
            // Remove loading indicator
            if (loadingElement && loadingElement.parentNode) {
                loadingElement.remove();
            }

            if (!response.ok) {
                throw new Error(data.error || 'Failed to get response');
            }

            // Display bot response
            if (data.answer) {
                displayMessage(data.answer, 'bot', new Date().toISOString());
            } else {
                throw new Error('Empty response from server');
            }

        } catch (error) {
            console.error('Error:', error);
            displayErrorMessage(error.message);
        } finally {
            isProcessing = false;
            scrollToBottom();
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

    // Helper function to display error messages
    function displayErrorMessage(message = 'An error occurred. Please try again.') {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chat-message error-message';
        errorDiv.innerHTML = `
            <div class="markdown-content">
                <p>⚠️ ${message}</p>
            </div>
            <small class="timestamp">${formatTimestamp(new Date())}</small>
        `;
        chatBody.appendChild(errorDiv);
        scrollToBottom();
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

    function disableInput() {
        userInput.disabled = true;
        sendButton.disabled = true;
    }

    function enableInput() {
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }

    async function makeSessionNameEditable(sessionElement, sessionId) {
        const nameSpan = sessionElement.querySelector('.session-name');
        if (!nameSpan) return; // Guard clause
        
        const originalName = nameSpan.textContent;
        console.log('Starting rename for session:', sessionId, 'Original name:', originalName); // Debug log

        const input = document.createElement('input');
        input.type = 'text';
        input.value = originalName;
        input.className = 'session-name-input';
        
        nameSpan.replaceWith(input);
        input.focus();
        input.select();

        const saveChanges = async () => {
            const newName = input.value.trim() || originalName;
            console.log('Attempting to save new name:', newName); // Debug log

            try {
                const response = await fetch('/api/rename_session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken() // Make sure to get CSRF token if needed
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        new_name: newName
                    })
                });

                console.log('Rename response status:', response.status); // Debug log

                if (response.ok) {
                    const data = await response.json();
                    console.log('Rename successful:', data); // Debug log

                    const newSpan = document.createElement('span');
                    newSpan.className = 'session-name';
                    newSpan.textContent = newName;
                    input.replaceWith(newSpan);

                    // Update session name in the list
                    sessionElement.querySelector('.session-name').textContent = newName;

                    // Reattach double-click handler
                    newSpan.addEventListener('dblclick', (e) => {
                        e.stopPropagation();
                        makeSessionNameEditable(sessionElement, sessionId);
                    });

                } else {
                    const errorData = await response.json();
                    console.error('Rename failed:', errorData); // Debug log
                    restoreOriginalName();
                    showError('Failed to rename session. Please try again.');
                }
            } catch (error) {
                console.error('Error during rename:', error); // Debug log
                restoreOriginalName();
                showError('Network error occurred. Please try again.');
            }
        };

        const restoreOriginalName = () => {
            const newSpan = document.createElement('span');
            newSpan.className = 'session-name';
            newSpan.textContent = originalName;
            input.replaceWith(newSpan);

            // Reattach double-click handler
            newSpan.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                makeSessionNameEditable(sessionElement, sessionId);
            });
        };

        // Remove existing event listeners before adding new ones
        input.addEventListener('blur', () => {
            // Small timeout to allow Enter key event to fire first
            setTimeout(saveChanges, 100);
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveChanges();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                restoreOriginalName();
            }
        });
    }

    // Helper function to show errors
    function showError(message) {
        // Implement your error display logic here
        console.error(message);
        // You could show a toast notification or alert
    }

    // Helper function to get CSRF token if needed
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }

    async function updateSessionName(sessionId, firstMessage) {
        try {
            const response = await fetch('/rename_chat_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    new_name: firstMessage
                })
            });

            if (!response.ok) throw new Error('Failed to update session name');

            // Update session name in sidebar
            const sessionElement = document.querySelector(`[data-chat-id="${sessionId}"]`);
            if (sessionElement) {
                const nameSpan = sessionElement.querySelector('.session-name');
                if (nameSpan) nameSpan.textContent = firstMessage;
            }
        } catch (error) {
            console.error('Error updating session name:', error);
        }
    }

    // Improved input resize function
    function adjustTextAreaHeight(textarea) {
        // Store scroll position
        const scrollPos = textarea.scrollTop;
        
        // Reset height to default
        textarea.style.height = '48px';
        
        // Calculate required height based on content
        const contentHeight = textarea.scrollHeight;
        
        if (textarea.value.length === 0) {
            // Reset to default height if empty
            textarea.style.height = '48px';
            textarea.style.overflowY = 'hidden';
        } else if (contentHeight <= 48) {
            // Keep at default height if content is small
            textarea.style.height = '48px';
            textarea.style.overflowY = 'hidden';
        } else if (contentHeight > 150) {
            // Cap at max height and enable scrolling
            textarea.style.height = '150px';
            textarea.style.overflowY = 'auto';
        } else {
            // Grow with content
            textarea.style.height = contentHeight + 'px';
            textarea.style.overflowY = 'hidden';
        }
        
        // Restore scroll position
        textarea.scrollTop = scrollPos;
    }

    // Add these event listeners
    userInput.addEventListener('input', function() {
        adjustTextAreaHeight(this);
    });

    userInput.addEventListener('keyup', function(e) {
        if (e.key === 'Backspace' || e.key === 'Delete') {
            adjustTextAreaHeight(this);
        }
    });

    // Reset input field
    function clearInput() {
        userInput.value = '';
        userInput.style.height = '48px';
        userInput.style.overflowY = 'hidden';
    }

    // Initialize input height when page loads
    userInput.style.height = '48px';

    // Add this to handle paste events
    userInput.addEventListener('paste', function() {
        setTimeout(() => adjustTextAreaHeight(this), 0);
    });
});