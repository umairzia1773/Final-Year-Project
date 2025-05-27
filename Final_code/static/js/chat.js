console.log('chat.js file loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat.js initialized');

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
    const attachmentPreview = document.querySelector('.attachment-preview');
    const fileName = attachmentPreview?.querySelector('.file-name');
    const removeFileBtn = attachmentPreview?.querySelector('.remove-file');
    const profileBtn = document.getElementById('profile-btn');

    // Add session storage variables
    let isNewLogin = !sessionStorage.getItem('wasLoggedIn');
    sessionStorage.setItem('wasLoggedIn', 'true');

    // Log if elements are found
    console.log('Elements initialized:', {
        attachmentBtn: !!attachmentBtn,
        fileInput: !!fileInput,
        attachmentPreview: !!attachmentPreview,
        fileName: !!fileName,
        removeFileBtn: !!removeFileBtn
    });

    // Test direct event handlers
    if (attachmentBtn) {
        attachmentBtn.addEventListener('click', function(e) {
            console.log('Attachment button clicked');
            e.preventDefault();
            e.stopPropagation();
            if (fileInput) {
                fileInput.click();
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            console.log('File input changed');
            const file = e.target.files[0];
            if (file) {
                console.log('Selected file:', file.name);
                
                if (file.type !== 'application/pdf') {
                    console.log('Invalid file type:', file.type);
                    alert('Please select a PDF file');
                    fileInput.value = '';
                    return;
                }

                // Show loading state
                if (attachmentBtn) {
                    attachmentBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                }

                const formData = new FormData();
                formData.append('file', file);

                // Upload file
                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    console.log('Upload response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Upload response data:', data);
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }

                    // Store the file context
                    currentFileContext = data.context;
                    console.log('File context stored:', currentFileContext ? 'yes' : 'no');

                    // Update UI
                    if (fileName && attachmentPreview) {
                        fileName.textContent = file.name;
                        attachmentPreview.classList.add('show');
                        console.log('Preview updated with filename:', file.name);
                    } else {
                        console.error('Preview elements not found');
                    }
                })
                .catch(error => {
                    console.error('Error uploading file:', error);
                    alert('Failed to upload file. Please try again.');
                })
                .finally(() => {
                    if (attachmentBtn) {
                        attachmentBtn.innerHTML = '<i class="fas fa-paperclip"></i>';
                    }
                });
            }
        });
    }

    // Handle remove file button
    if (removeFileBtn && attachmentPreview) {
        removeFileBtn.addEventListener('click', function() {
            console.log('Remove file clicked');
            if (fileInput) {
                fileInput.value = '';
            }
            currentFileContext = null; // Clear the file context
            attachmentPreview.classList.remove('show');
        });
    }

    // Initialize chat history
    async function initializeChatHistory() {
        try {
            const response = await fetch('/get_user_chat_sessions');
            if (!response.ok) {
                throw new Error('Failed to fetch chat sessions');
            }

            const data = await response.json();
            
            if (data.length === 0) {
                displayWelcomeScreen();
                return;
            }

            // Handle session restoration
            if (!isNewLogin) {
                // Get last active session from localStorage
                const lastSessionId = localStorage.getItem('lastActiveSession');
                if (lastSessionId) {
                    // Find the session in the data
                    const lastSession = data.find(session => session.session_id === lastSessionId);
                    if (lastSession) {
                        // Restore the last active session
                        currentChatSessionId = lastSessionId;
                        loadChatHistory(lastSessionId);
                        return;
                    }
                }
            }

            // If it's a new login or no previous session found, start a new chat
            displayWelcomeScreen();
        } catch (error) {
            console.error('Error initializing chat history:', error);
            displayWelcomeScreen();
        }
    }

    // State
    let currentChatSessionId = null;
    let userId = document.body.getAttribute('data-user-id');
    let isProcessing = false;
    let darkTheme = localStorage.getItem('darkTheme') === 'true';
    let sentMessages = new Set();
    let isWaitingForResponse = false;
    let currentAttachedFile = null;
    let currentFileContext = null;
    let lastScrapingMessage = '';

    // Initialize
    initializeTheme();
    loadChatSessions();
    setupEventListeners();

    // Add direct click handler to verify button is clickable
    if (attachmentBtn) {
        attachmentBtn.onclick = (e) => {
            console.log('Attachment button clicked directly');
            e.preventDefault();
            if (fileInput) {
                fileInput.click();
            } else {
                console.error('File input not found');
            }
        };
    } else {
        console.error('Attachment button not found');
    }

    // Add direct change handler to verify file input works
    if (fileInput) {
        fileInput.onchange = (event) => {
            console.log('File input changed directly');
            const file = event.target.files[0];
            if (file) {
                console.log('File selected:', file.name);
            }
        };
    } else {
        console.error('File input not found');
    }

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

        // Create profile dropdown
        const profileDropdown = document.createElement('div');
        profileDropdown.className = 'profile-dropdown';

        // Get user email from data attribute
        const userEmail = document.body.getAttribute('data-user-email');

        profileDropdown.innerHTML = `
            <div class="profile-info">
                <i class="fas fa-user-circle"></i>
                <span>${userEmail || 'User'}</span>
            </div>
            <a href="/logout" class="dropdown-item">
                <i class="fas fa-sign-out-alt"></i>
                Logout
            </a>
        `;

        document.body.appendChild(profileDropdown);

        // Toggle profile dropdown
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profileDropdown.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!profileDropdown.contains(e.target) && !profileBtn.contains(e.target)) {
                profileDropdown.classList.remove('show');
            }
        });

        // File upload button click
        attachmentBtn.addEventListener('click', (e) => {
            console.log('Attachment button clicked'); // Debug log
            e.preventDefault();
            fileInput.click();
        });

        // File selected handler
        fileInput.addEventListener('change', async (event) => {
            console.log('File input change event triggered'); // Debug log
            const file = event.target.files[0];
            if (!file) {
                console.log('No file selected'); // Debug log
                return;
            }

            console.log('Selected file:', file.name, 'Type:', file.type); // Debug log

            if (file.type !== 'application/pdf') {
                alert('Please select a PDF file');
                fileInput.value = '';
                return;
            }

            try {
                // Show loading state
                attachmentBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                console.log('Uploading file...'); // Debug log
                
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                console.log('Upload response status:', response.status); // Debug log
                const data = await response.json();
                console.log('Upload response data:', data); // Debug log

                if (!response.ok) {
                    throw new Error(data.error || 'Upload failed');
                }

                // Update UI to show attached file
                currentAttachedFile = file.name;
                console.log('Setting current attached file:', currentAttachedFile); // Debug log
                
                // Get the preview elements
                const attachmentPreview = document.querySelector('.attachment-preview');
                const fileName = attachmentPreview.querySelector('.file-name');
                
                console.log('Updating preview elements'); // Debug log
                // Update file name and show preview
                fileName.textContent = file.name;
                attachmentPreview.classList.add('show');
                
                // Store the context
                currentFileContext = data.context;

                // Add remove file handler
                const removeFileBtn = attachmentPreview.querySelector('.remove-file');
                removeFileBtn.onclick = (e) => {
                    console.log('Remove button clicked'); // Debug log
                    e.stopPropagation(); // Prevent event bubbling
                    currentAttachedFile = null;
                    currentFileContext = null;
                    attachmentPreview.classList.remove('show');
                    fileInput.value = ''; // Clear the file input
                    fileName.textContent = ''; // Clear the file name
                };

            } catch (error) {
                console.error('Error uploading file:', error);
                alert('Failed to upload file. Please try again.');
                // Reset file input
                fileInput.value = '';
            } finally {
                // Reset attachment button
                attachmentBtn.innerHTML = '<i class="fas fa-paperclip"></i>';
            }
        });

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
    async function loadChatSessions() {
        try {
            const response = await fetch('/get_user_chat_sessions');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const historyList = document.getElementById('history-list');
            historyList.innerHTML = '';

            if (data.length === 0) {
                displayWelcomeScreen();
                return;
            }

            // Create and append session elements
            data.forEach(session => {
                const li = createSessionElement(session);
                historyList.appendChild(li);
            });

            // Handle session restoration
            if (!isNewLogin) {
                const lastSessionId = localStorage.getItem('lastActiveSession');
                if (lastSessionId) {
                    const lastActiveSession = document.querySelector(`.chat-session-item[data-chat-id="${lastSessionId}"]`);
                    if (lastActiveSession) {
                        lastActiveSession.classList.add('active');
                        loadChatHistory(lastSessionId);
                        return;
                    }
                }
            }

            // If no session to restore or new login, activate first session
            const firstSession = document.querySelector('.chat-session-item');
            if (firstSession) {
                firstSession.classList.add('active');
                const sessionId = firstSession.getAttribute('data-chat-id');
                if (sessionId) {
                    currentChatSessionId = sessionId;
                    loadChatHistory(sessionId);
                }
            }

        } catch (error) {
            console.error('Error loading chat sessions:', error);
            displayWelcomeScreen();
        }
    }

    // Add helper function to activate first session
    function activateFirstSession(data) {
        if (data && data.length > 0) {
            const firstSession = data[0];
            const firstSessionElement = document.querySelector('.chat-session-item');
            if (firstSessionElement) {
                firstSessionElement.classList.add('active');
                loadChatHistory(firstSession.session_id);
            }
        }
    }

    // Add retry function
    function retryLoadSessions() {
        loadChatSessions();
    }

    // Add helper function to create session elements
    function createSessionElement(session) {
                    const li = document.createElement('li');
                    li.className = 'chat-session-item';
                    li.setAttribute('data-chat-id', session.session_id);

        // Safely get session name
        let displayName = session.session_name || 'New Chat';
        if (displayName.length > 25) {
            displayName = displayName.substring(0, 25) + '...';
                    }

                    li.innerHTML = `
                        <div class="chat-session-title">
                            <i class="fas fa-comments"></i>
                <span class="session-name">${displayName}</span>
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

        // Add click handler
        li.addEventListener('click', function(e) {
            if (!e.target.closest('.chat-session-menu') && 
                !e.target.classList.contains('session-name-input')) {
                handleSessionClick(this, session.session_id);
            }
        });

        // Setup other event listeners
        setupSessionEventListeners(li);

        return li;
    }

    // Load chat history for a specific session
    async function loadChatHistory(sessionId) {
        if (!sessionId) {
            console.error('No session ID provided');
            return;
        }

        // Update current session ID and localStorage
        currentChatSessionId = sessionId;
        localStorage.setItem('lastActiveSession', sessionId);

        // Clear and show loading state
        const chatBody = document.getElementById('chat-body');
        chatBody.innerHTML = `
            <div class="loading-indicator">
                <div class="loading-dots">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>`;

        try {
            const response = await fetch(`/get_chat_history?session_id=${sessionId}`);
            if (!response.ok) throw new Error('Failed to fetch chat history');
            
            const data = await response.json();
            chatBody.innerHTML = ''; // Clear loading indicator

            if (!Array.isArray(data) || data.length === 0) {
                // Show empty state or welcome message
                chatBody.innerHTML = `
                    <div class="welcome-message">
                        <h2>Start a New Conversation</h2>
                        <p>Send a message to begin chatting with AI Assistant.</p>
                    </div>`;
                return;
            }

            // Sort messages by timestamp
            data.sort((a, b) => {
                const timeA = new Date(a.created_at).getTime();
                const timeB = new Date(b.created_at).getTime();
                return timeA - timeB;
            });

            // Display messages
            data.forEach(message => {
                if (message.message && message.sender) {
                    displayMessage(message.message, message.sender, message.created_at);
                }
            });

            // Scroll to bottom after loading messages
            scrollToBottom();

        } catch (error) {
            console.error('Error loading chat history:', error);
            chatBody.innerHTML = `
                <div class="error-message">
                    <p>Failed to load chat history. Please try again.</p>
                    <button onclick="retryLoadHistory('${sessionId}')" class="retry-btn">
                        Retry
                    </button>
                </div>`;
        }
    }

    // Add retry function
    function retryLoadHistory(sessionId) {
        if (sessionId) {
            loadChatHistory(sessionId);
        }
    }

    // Update the session click handler
    function handleSessionClick(sessionElement, sessionId) {
        // Remove active class from all sessions
        document.querySelectorAll('.chat-session-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to clicked session
        sessionElement.classList.add('active');
        
        // Load chat history
        loadChatHistory(sessionId);
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
        const sessionId = sessionElement.getAttribute('data-chat-id');
        const menuBtn = sessionElement.querySelector('.menu-btn');
        const menuDropdown = sessionElement.querySelector('.session-menu-dropdown');
        const nameSpan = sessionElement.querySelector('.session-name');
        const renameBtn = sessionElement.querySelector('.rename-btn');
        const deleteBtn = sessionElement.querySelector('.delete-btn');

        // Double-click to rename
        nameSpan.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            makeSessionNameEditable(sessionElement, sessionId);
        });

        // Menu button toggle
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menuDropdown.classList.toggle('show');
        });

        // Rename button click
        renameBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menuDropdown.classList.remove('show');
            makeSessionNameEditable(sessionElement, sessionId);
        });

        // Delete button click
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menuDropdown.classList.remove('show');
            showDeleteConfirmation(sessionId, sessionElement);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            menuDropdown.classList.remove('show');
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
            localStorage.removeItem('lastActiveSession');
            
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

    // Add format selection UI
    function showFormatSelection(options) {
        const formatSelectionHtml = `
            <div class="format-selection-message bot-message">
                <p>${options.message}</p>
                <div class="format-options">
                    ${options.options.map(format => `
                        <button class="format-option" data-format="${format}">
                            <i class="fas fa-file"></i> ${format.toUpperCase()}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        chatBody.insertAdjacentHTML('beforeend', formatSelectionHtml);
        
        // Add event listeners to format buttons
        const formatButtons = document.querySelectorAll('.format-option');
        formatButtons.forEach(button => {
            button.addEventListener('click', () => {
                const selectedFormat = button.getAttribute('data-format');
                handleFormatSelection(selectedFormat);
            });
        });
        
        scrollToBottom();
    }

    // Add loading animation function
    function showLoadingMessage() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message bot-message loading-message';
        loadingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            <div class="loading-text">AI is processing your request...</div>
        `;
        chatBody.appendChild(loadingDiv);
        scrollToBottom();
        return loadingDiv;
    }

    // Update sendMessage function
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message || isProcessing) return;

        try {
            isProcessing = true;
            disableInput();

            // Remove welcome screen if it exists
            const welcomeContainer = chatBody.querySelector('.welcome-container');
            if (welcomeContainer) {
                welcomeContainer.remove();
            }

            // Display user message
            displayMessage(message, 'user');
            
            // Store scraping message if it's a scraping request
            if (message.toLowerCase().includes('scrape')) {
                lastScrapingMessage = message;
            }
            
            // Clear input
            clearInput();

            // Show loading animation
            const loadingMessage = showLoadingMessage();

            // Create new chat session if needed
            if (!currentChatSessionId) {
                const sessionData = await createNewChat(message);
                currentChatSessionId = sessionData.session_id;
            }

            // Send message to server
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: currentChatSessionId,
                    file_context: currentFileContext
                })
            });

            const data = await response.json();
            
            // Remove loading animation
            loadingMessage.remove();
            
            if (data.error) {
                displayErrorMessage(data.error);
                return;
            }

            // Check if format selection is needed
            if (data.type === 'format_selection') {
                showFormatSelection(data);
                return;
            }

            // Display the bot's response
            displayMessage(data.answer, 'bot');

        } catch (error) {
            console.error('Error:', error);
            displayErrorMessage();
        } finally {
            isProcessing = false;
            enableInput();
            scrollToBottom();
        }
    }

    // Update handleFormatSelection function
    async function handleFormatSelection(selectedFormat) {
        if (!lastScrapingMessage) {
            displayErrorMessage('Could not find the original scraping request. Please try again.');
            return;
        }
        
        // Show loading state
        disableInput();
        const loadingMessage = showLoadingMessage();
        
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: lastScrapingMessage,
                    session_id: currentChatSessionId,
                    selected_format: selectedFormat,
                    file_context: currentFileContext
                })
            });
            
            const data = await response.json();
            
            // Remove loading animation
            loadingMessage.remove();
            
            if (data.error) {
                displayErrorMessage(data.error);
                return;
            }
            
            // Display the response
            displayMessage(data.answer, 'bot');
            
            // Clear the stored scraping message after successful processing
            lastScrapingMessage = '';
            
        } catch (error) {
            console.error('Error:', error);
            displayErrorMessage('Failed to process the request. Please try again.');
        } finally {
            enableInput();
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

    // Delete confirmation modal
    function showDeleteConfirmation(sessionId, sessionElement) {
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'confirmation-modal';
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3 class="modal-title">Delete Chat</h3>
            </div>
            <div class="modal-body">
                <p class="modal-message">Are you sure you want to delete this chat? This action cannot be undone.</p>
            </div>
            <div class="modal-buttons">
                <button class="modal-btn cancel">Cancel</button>
                <button class="modal-btn delete">Delete</button>
            </div>
        `;
        
        modalOverlay.appendChild(modalContent);
        document.body.appendChild(modalOverlay);

        const closeModal = () => modalOverlay.remove();

        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closeModal();
        });

        modalContent.querySelector('.cancel').addEventListener('click', closeModal);

        modalContent.querySelector('.delete').addEventListener('click', async () => {
            try {
                const response = await fetch('/delete_chat_session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ session_id: sessionId })
                });

                if (response.ok) {
                    sessionElement.remove();
                    if (currentChatSessionId === sessionId) {
                        currentChatSessionId = null;
                        chatBody.innerHTML = '';
                        displayWelcomeScreen();
                    }
                }
            } catch (error) {
                console.error('Error deleting chat:', error);
            } finally {
                closeModal();
            }
        });
    }

    // Improved rename functionality
    async function makeSessionNameEditable(sessionElement, sessionId) {
        const nameSpan = sessionElement.querySelector('.session-name');
        if (!nameSpan || nameSpan.querySelector('input')) return;
        
        const originalName = nameSpan.textContent;

        // Create input with enhanced styling
        const input = document.createElement('input');
        input.type = 'text';
        input.value = originalName;
        input.className = 'session-name-input';
        
        // Add transition wrapper
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.appendChild(input);
        
        nameSpan.innerHTML = '';
        nameSpan.appendChild(wrapper);
        
        input.focus();
        input.select();

        // Add visual feedback
        input.style.animation = 'fadeIn 0.2s ease';

        const saveChanges = async () => {
            const newName = input.value.trim();
            if (!newName || newName === originalName) {
                restoreOriginalName();
                return;
            }

            try {
                const response = await fetch('/rename_chat_session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        new_name: newName
                    })
                });

                    const data = await response.json();
                
                if (response.ok && data.success) {
                    nameSpan.textContent = newName;
                    // Refresh the sessions list to ensure consistency
                    loadChatSessions();
                } else {
                    throw new Error(data.error || 'Failed to rename chat');
                }
            } catch (error) {
                console.error('Error renaming chat:', error);
                restoreOriginalName();
            }
        };

        const restoreOriginalName = () => {
            nameSpan.textContent = originalName;
        };

        input.addEventListener('blur', saveChanges);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                input.blur();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                restoreOriginalName();
            }
        });

        input.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // Add function to refresh sessions periodically or after updates
    function refreshSessions() {
        loadChatSessions();
    }

    // Call refreshSessions after successful rename or delete
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM Content Loaded'); // Debug log
        
        // Ensure history-list exists
        const historyList = document.getElementById('history-list');
        if (!historyList) {
            console.error('History list element not found on page load');
            return;
        }

        // Initial load
        loadChatSessions();

        // Add refresh button to header for manual refresh
        const headerRight = document.querySelector('.header-right');
        if (headerRight) {
            const refreshButton = document.createElement('button');
            refreshButton.className = 'refresh-btn';
            refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
            refreshButton.onclick = loadChatSessions;
            headerRight.insertBefore(refreshButton, headerRight.firstChild);
        }
    });

    // Add these styles
    const styles = `
    .session-name-input {
        background: transparent;
        border: none;
        border-bottom: 2px solid var(--primary-color);
        padding: 2px 4px;
        margin: -2px -4px;
        font-size: inherit;
        font-family: inherit;
        color: white;
        width: calc(100% - 8px);
        outline: none;
    }

    .session-name-input:focus {
        background: rgba(255, 255, 255, 0.1);
    }

    /* Dark theme support */
    [data-theme="dark"] .session-name-input {
        color: white;
        background: transparent;
    }

    /* Update logout button text visibility */
    .profile-dropdown .dropdown-item {
        color: var(--text-primary) !important;
    }

    /* Update loading animation for dark theme */
    [data-theme="dark"] .typing-dot {
        background: #fff;
        opacity: 0.8;
    }

    [data-theme="dark"] .loading-text {
        color: #fff;
        opacity: 0.8;
    }

    [data-theme="dark"] .loading-indicator {
        background: rgba(255, 255, 255, 0.1);
    }

    [data-theme="dark"] .loading-dots .dot {
        background-color: #fff;
        opacity: 0.8;
    }

    /* Ensure loading animation is visible in both themes */
    .loading-dots .dot {
        width: 8px;
        height: 8px;
        margin: 0 4px;
        border-radius: 50%;
        display: inline-block;
        animation: bounce 1.4s infinite ease-in-out both;
    }

    .loading-dots .dot:nth-child(1) {
        animation-delay: -0.32s;
    }

    .loading-dots .dot:nth-child(2) {
        animation-delay: -0.16s;
    }

    @keyframes bounce {
        0%, 80%, 100% { 
            transform: scale(0);
        } 
        40% { 
            transform: scale(1.0);
        }
    }

    .chat-session-item.active {
        background-color: rgba(255, 255, 255, 0.1) !important;
        font-weight: 600;
    }

    .chat-session-item.active .session-name {
        color: white;
    }

    .loading-indicator {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
        margin: 20px 0;
    }

    .welcome-message {
        text-align: center;
        padding: 40px 20px;
        color: var(--text-secondary);
    }

    .welcome-message h2 {
        margin-bottom: 12px;
        color: var(--text-primary);
    }

    .error-message {
        padding: 20px;
        margin: 10px;
        background: rgba(220, 38, 38, 0.1);
        border-radius: 8px;
        text-align: center;
    }

    .retry-btn {
        margin-top: 10px;
        padding: 8px 16px;
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .retry-btn:hover {
        opacity: 0.9;
    }

    .refresh-btn {
        background: none;
        border: none;
        color: var(--text-primary);
        padding: 8px;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .refresh-btn:hover {
        background: var(--bg-secondary);
    }

    .refresh-btn i {
        font-size: 16px;
    }

    .format-selection-message {
        width: fit-content !important;
        max-width: 80% !important;
    }
    
    .format-options {
        display: flex;
        gap: 10px;
        margin-top: 15px;
        flex-wrap: wrap;
    }
    
    .format-option {
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        background-color: var(--primary-color);
        color: white;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 80px;
        justify-content: center;
    }
    
    .format-option:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 36, 107, 0.2);
    }
    
    [data-theme="dark"] .format-option {
        background-color: var(--bg-secondary);
    }
    
    [data-theme="dark"] .format-option:hover {
        background-color: var(--primary-color);
    }
    `;

    // Add additional styles
    const additionalStyles = `
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
        background: var(--bg-secondary);
        border-radius: 12px;
        width: fit-content;
        margin-bottom: 8px;
    }

    .typing-dot {
        width: 8px;
        height: 8px;
        background: var(--primary-color);
        border-radius: 50%;
        animation: typing-bounce 1.4s infinite;
        opacity: 0.6;
    }

    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }

    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes typing-bounce {
        0%, 60%, 100% {
            transform: translateY(0);
        }
        30% {
            transform: translateY(-4px);
        }
    }

    .loading-text {
        font-size: 0.9em;
        color: var(--text-secondary);
        margin-top: 4px;
    }

    .loading-message {
        opacity: 0.8;
    }
    `;

    // Add styles to document
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles + additionalStyles;
    document.head.appendChild(styleSheet);

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

    function saveCurrentSessionState() {
        if (currentChatSessionId) {
            localStorage.setItem('lastActiveSession', currentChatSessionId);
            // Save scroll position
            const chatBody = document.getElementById('chat-body');
            localStorage.setItem('chatScrollPosition', chatBody.scrollTop);
        }
    }

    function restoreSessionState() {
        const lastSessionId = localStorage.getItem('lastActiveSession');
        if (lastSessionId) {
            currentChatSessionId = lastSessionId;
            
            // First highlight the active session
            const activeSession = document.querySelector(`.chat-session-item[data-chat-id="${lastSessionId}"]`);
            if (activeSession) {
                // Remove active class from all sessions
                document.querySelectorAll('.chat-session-item').forEach(item => {
                    item.classList.remove('active');
                });
                // Add active class to current session
                activeSession.classList.add('active');
                
                // Load the chat history
                loadChatHistory(lastSessionId).then(() => {
                    // Restore scroll position after chat history is loaded
                    const savedScrollPosition = localStorage.getItem('chatScrollPosition');
                    if (savedScrollPosition) {
                        const chatBody = document.getElementById('chat-body');
                        chatBody.scrollTop = parseInt(savedScrollPosition);
                    }
                });
            }
        }
    }

    // Update window beforeunload event to save session state
    window.addEventListener('beforeunload', function() {
        if (currentChatSessionId) {
            localStorage.setItem('lastActiveSession', currentChatSessionId);
            localStorage.setItem('lastScrollPosition', chatBody.scrollTop);
        }
    });
});