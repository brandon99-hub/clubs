// Real-time messaging functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token for AJAX requests
    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Initialize messaging if we're on a messaging page
    if (typeof roomName !== 'undefined' && roomName && typeof username !== 'undefined') {
        initializeMessaging();
    }

    function initializeMessaging() {
        let chatSocket = null;
        let isConnected = false;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        // DOM elements
        const messageForm = document.querySelector('form[method="post"]');
        const messageInput = document.getElementById('message-input');
        const messageContainer = document.getElementById('chat-area');
        const typingIndicator = document.getElementById('typing-indicator');
        const submitButton = messageForm ? messageForm.querySelector('button[type="submit"]') : null;

        // Initialize WebSocket connection
        function connectWebSocket() {
            try {
                chatSocket = new WebSocket(
                    'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
                );

                chatSocket.onopen = function(e) {
                    console.log('WebSocket connected successfully');
                    isConnected = true;
                    reconnectAttempts = 0;
                    updateConnectionStatus(true);
                };

                chatSocket.onerror = function(e) {
                    console.error('WebSocket error occurred:', e);
                    isConnected = false;
                    updateConnectionStatus(false);
                };

                chatSocket.onclose = function(e) {
                    console.log('WebSocket connection closed. Code:', e.code, 'Reason:', e.reason);
                    isConnected = false;
                    updateConnectionStatus(false);
                    
                    // Attempt to reconnect if not a normal closure
                    if (e.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
                        reconnectAttempts++;
                        console.log(`Attempting to reconnect... (${reconnectAttempts}/${maxReconnectAttempts})`);
                        setTimeout(connectWebSocket, 2000 * reconnectAttempts);
                    }
                };

                chatSocket.onmessage = function(e) {
                    try {
                        const data = JSON.parse(e.data);
                        console.log('WebSocket data received:', data);

                        // Handle typing indicators
                        if ("typing" in data) {
                            handleTypingIndicator(data);
                        }

                        // Handle chat messages
                        if ("message" in data) {
                            displayMessage(data.message, data.username, false);
                        }

                        // Handle errors
                        if ("error" in data) {
                            showError(data.error);
                        }
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };
            } catch (error) {
                console.error('Error creating WebSocket connection:', error);
                updateConnectionStatus(false);
            }
        }

        // Update connection status UI
        function updateConnectionStatus(connected) {
            const statusIndicator = document.getElementById('connection-status');
            if (statusIndicator) {
                statusIndicator.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
                statusIndicator.className = connected ? 'text-success' : 'text-danger';
            }
        }

        // Handle typing indicators
        function handleTypingIndicator(data) {
            if (typingIndicator) {
                if (data.typing && data.username !== username) {
                    typingIndicator.textContent = `${data.username} is typing...`;
                    typingIndicator.style.display = 'block';
                } else {
                    typingIndicator.textContent = '';
                    typingIndicator.style.display = 'none';
                }
            }
        }

        // Display a message in the chat area
        function displayMessage(message, senderUsername, isOwnMessage = false, timestamp = null) {
            if (!messageContainer) return;

            const messageDiv = document.createElement("div");
            messageDiv.classList.add(
                "chat-message",
                isOwnMessage ? "text-end" : "text-start",
                "mb-3"
            );

            const displayName = isOwnMessage ? "You" : senderUsername;
            const messageClass = isOwnMessage ? "bg-primary text-white" : "bg-light text-dark";

            // Convert backend UTC timestamp to local time if provided
            let timeString = '';
            if (timestamp) {
                const dateObj = new Date(timestamp);
                timeString = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            } else {
                timeString = new Date().toLocaleTimeString();
            }

            messageDiv.innerHTML = `
                <div class="${messageClass} p-3 rounded-3 shadow-sm" style="max-width: 75%;">
                    <p class="mb-1"><strong>${displayName}:</strong> ${escapeHtml(message)}</p>
                    <small class="${isOwnMessage ? 'text-light' : 'text-muted'}">${timeString}</small>
                </div>
            `;

            messageContainer.appendChild(messageDiv);
            
            // Always scroll to bottom after adding a message
            scrollToBottom();
        }

        // Escape HTML to prevent XSS
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Scroll chat to bottom
        function scrollToBottom() {
            if (messageContainer) {
                // Use setTimeout to ensure DOM is updated before scrolling
                setTimeout(() => {
                    messageContainer.scrollTop = messageContainer.scrollHeight;
                }, 10);
            }
        }

        // Initial scroll to bottom on page load
        scrollToBottom();

        // Show error message
        function showError(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger alert-dismissible fade show';
            errorDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            const container = document.querySelector('.container');
            if (container) {
                container.insertBefore(errorDiv, container.firstChild);
            }
        }

        // Send message via WebSocket
        function sendMessageViaWebSocket(message) {
            if (chatSocket && isConnected) {
                const data = {
                    message: message,
                    username: username
                };
                chatSocket.send(JSON.stringify(data));
                return true;
            }
            return false;
        }

        // Save message to database via AJAX
        async function saveMessageToDatabase(message) {
            try {
                const response = await fetch(`/club/${getClubIdFromUrl()}/save_message/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        content: message
                    })
                });

                const data = await response.json();
                
                if (response.ok && data.success) {
                    console.log('Message saved to database:', data);
                    return data; // Return the whole data object for timestamp
                } else {
                    console.error('Failed to save message:', data.error);
                    showError('Failed to save message: ' + (data.error || 'Unknown error'));
                    return false;
                }
            } catch (error) {
                console.error('Error saving message to database:', error);
                showError('Network error while saving message');
                return false;
            }
        }

        // Get club ID from URL
        function getClubIdFromUrl() {
            const match = window.location.pathname.match(/\/club\/(\d+)\//);
            return match ? match[1] : null;
        }

        // Handle form submission
        if (messageForm) {
            messageForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const message = messageInput.value.trim();
                if (!message) return;

                // Show loading spinner if available
                const loadingSpinner = document.getElementById('loadingSpinner');
                if (loadingSpinner) loadingSpinner.style.display = 'block';

                // Disable form during submission
                if (submitButton) submitButton.disabled = true;
                messageInput.disabled = true;

                try {
                    // Save to database in background and get timestamp
                    const dbSaved = await saveMessageToDatabase(message);
                    let backendTimestamp = null;
                    if (dbSaved && dbSaved.timestamp) {
                        backendTimestamp = dbSaved.timestamp;
                    }

                    // Display message immediately for better UX, using backend timestamp if available
                    displayMessage(message, username, true, backendTimestamp);
                    
                    // Clear input
                    messageInput.value = '';

                    // Send via WebSocket for real-time delivery
                    const webSocketSent = sendMessageViaWebSocket(message);

                    if (!webSocketSent) {
                        showError('Real-time messaging is currently unavailable. Message saved to database.');
                    }

                    if (!dbSaved) {
                        showError('Message sent but failed to save to database.');
                    }

                } catch (error) {
                    console.error('Error sending message:', error);
                    showError('Failed to send message. Please try again.');
                } finally {
                    // Always hide spinner and re-enable form, regardless of success/error
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                    if (submitButton) submitButton.disabled = false;
                    if (messageInput) messageInput.disabled = false;
                }
            });
        }

        // Handle typing indicators
        let typingTimeout;
        if (messageInput) {
            messageInput.addEventListener('input', function() {
                if (chatSocket && isConnected) {
                    // Send typing indicator
                    const data = {
                        typing: true,
                        username: username
                    };
                    chatSocket.send(JSON.stringify(data));

                    // Clear previous timeout
                    clearTimeout(typingTimeout);

                    // Set timeout to stop typing indicator
                    typingTimeout = setTimeout(() => {
                        if (chatSocket && isConnected) {
                            const data = {
                                typing: false,
                                username: username
                            };
                            chatSocket.send(JSON.stringify(data));
                        }
                    }, 1000);
                }
            });
        }

        // Initialize WebSocket connection
        connectWebSocket();

        // Add connection status indicator to the page
        const statusDiv = document.createElement('div');
        statusDiv.id = 'connection-status';
        statusDiv.className = 'text-success small mb-2';
        statusDiv.textContent = '🟢 Connected';
        
        if (messageForm) {
            messageForm.parentNode.insertBefore(statusDiv, messageForm);
        }

        // Handle page unload
        window.addEventListener('beforeunload', function() {
            if (chatSocket) {
                chatSocket.close(1000, 'Page unload');
            }
        });
    }
}); 