// Real-time messaging functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize messaging if we're on a messaging page and roomName/username are defined
    if (typeof roomName !== 'undefined' && roomName && typeof username !== 'undefined') {
        initializeMessaging();
    }

    function initializeMessaging() {
        let chatSocket = null;
        let isConnected = false;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5; // Max times to try reconnecting

        // DOM elements
        const messageForm = document.querySelector('form[method="post"]'); // Assuming this is your message form
        const messageInput = document.getElementById('message-input');
        const messageContainer = document.getElementById('chat-area'); // Where messages are displayed
        const typingIndicator = document.getElementById('typing-indicator');
        const submitButton = messageForm ? messageForm.querySelector('button[type="submit"]') : null;
        // const loadingSpinner = document.getElementById('loadingSpinner'); // Optional: for visual feedback (Currently not used in new flow)

        // Function to generate a simple temporary ID for optimistic messages
        function generateTempId() {
            return `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }

        // Initialize WebSocket connection
        function connectWebSocket() {
            try {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                chatSocket = new WebSocket(
                    protocol + '//' + window.location.host + '/ws/chat/' + roomName + '/'
                );

                chatSocket.onopen = function(e) {
                    console.log('WebSocket connected successfully.');
                    isConnected = true;
                    reconnectAttempts = 0; // Reset attempts on successful connection
                    updateConnectionStatus(true);
                };

                chatSocket.onerror = function(e) {
                    console.error('WebSocket error occurred:', e);
                    // isConnected will be set to false in onclose
                };

                chatSocket.onclose = function(e) {
                    console.log('WebSocket connection closed. Code:', e.code, 'Reason:', e.reason);
                    isConnected = false;
                    updateConnectionStatus(false);
                    
                    // Attempt to reconnect if not a normal closure (1000) and within attempt limits
                    if (e.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
                        reconnectAttempts++;
                        const delay = Math.min(30000, 2000 * reconnectAttempts); // Exponential backoff with max delay
                        console.log(`Attempting to reconnect... (${reconnectAttempts}/${maxReconnectAttempts}) in ${delay/1000}s`);
                        setTimeout(connectWebSocket, delay);
                    } else if (reconnectAttempts >= maxReconnectAttempts) {
                        console.error('Max reconnection attempts reached. Please refresh the page.');
                        showError('Connection lost. Max reconnection attempts reached. Please refresh.');
                    }
                };

                chatSocket.onmessage = function(e) {
                    try {
                        const data = JSON.parse(e.data);
                        console.log('WebSocket data received:', data);

                        switch (data.type) {
                            case 'chat_message':
                                handleChatMessage(data);
                                break;
                            case 'typing':
                                handleTypingIndicator(data);
                                break;
                            case 'error':
                                handleErrorFromServer(data);
                                break;
                            default:
                                console.warn('Received unknown WebSocket message type:', data.type);
                        }
                    } catch (error) {
                        console.error('Error parsing WebSocket message or handling data:', error);
                    }
                };
            } catch (error) {
                console.error('Error creating WebSocket connection:', error);
                updateConnectionStatus(false); // Show disconnected status
            }
        }

        function handleChatMessage(data) {
            // data = { type: 'chat_message', id: db_id, message: content, username: sender, timestamp: iso_ts, temp_id: client_temp_id }
            const existingOptimisticMessage = data.temp_id ? document.querySelector(`[data-temp-id="${data.temp_id}"]`) : null;

            if (existingOptimisticMessage) {
                // This is a confirmation for an optimistically sent message
                updateOptimisticMessage(existingOptimisticMessage, data);
            } else {
                // This is a new message from another user (or sender if optimistic UI failed/disabled)
                displayMessage(data.message, data.username, data.username === username, data.timestamp, data.id);
            }
        }

        function updateOptimisticMessage(element, confirmedData) {
            // Update the optimistic message with confirmed data from the server
            element.dataset.messageId = confirmedData.id; // Store the actual DB ID
            element.classList.remove('optimistic-message'); // Remove any 'pending' styling

            // Update timestamp if displayed (small element within the message structure)
            const timeElement = element.querySelector('small');
            if (timeElement && confirmedData.timestamp) {
                const dateObj = new Date(confirmedData.timestamp);
                timeElement.textContent = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
            // Optionally, update other parts or remove loading indicators specific to this message
            const pendingIndicator = element.querySelector('.pending-indicator');
            if (pendingIndicator) pendingIndicator.remove();
        }

        function handleErrorFromServer(data) {
            // data = { type: 'error', error: 'message', temp_id: client_temp_id (optional) }
            showError(data.error); // Generic error display
            if (data.temp_id) {
                const failedMessageElement = document.querySelector(`[data-temp-id="${data.temp_id}"]`);
                if (failedMessageElement) {
                    failedMessageElement.classList.add('message-failed');
                    // Add a visual cue that this message failed, e.g., change color, add icon
                    const errorSpan = document.createElement('span');
                    errorSpan.className = 'text-danger small ms-2';
                    errorSpan.textContent = '(Failed)';

                    const messageContentParagraph = failedMessageElement.querySelector('p');
                    if (messageContentParagraph) {
                         messageContentParagraph.appendChild(errorSpan);
                    } else {
                         failedMessageElement.appendChild(errorSpan); // fallback
                    }
                }
            }
        }

        function updateConnectionStatus(connected) {
            const statusIndicator = document.getElementById('connection-status'); // Assuming you have an element for this
            if (statusIndicator) {
                statusIndicator.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
                statusIndicator.className = connected ? 'text-success small mb-2' : 'text-danger small mb-2';
            }
            if (submitButton) submitButton.disabled = !connected; // Disable send if not connected
        }

        function handleTypingIndicator(data) {
            // data = { type: 'typing', typing: boolean, username: sender }
            if (typingIndicator) {
                if (data.typing && data.username !== username) { // Don't show own typing
                    typingIndicator.textContent = `${escapeHtml(data.username)} is typing...`;
                    typingIndicator.style.display = 'block';
                } else {
                    typingIndicator.textContent = '';
                    typingIndicator.style.display = 'none';
                }
            }
        }

        // Display a message in the chat area
        // Parameters: message content, sender's username, boolean if it's own message, ISO timestamp, DB message ID, temporary ID
        function displayMessage(messageContent, senderUsername, isOwnMessage = false, isoTimestamp = null, dbId = null, tempId = null) {
            if (!messageContainer) return;

            const messageDiv = document.createElement("div");
            // Add common classes and alignment based on whether it's user's own message
            messageDiv.classList.add("chat-message", isOwnMessage ? "text-end" : "text-start", "mb-3", "d-flex", isOwnMessage ? "justify-content-end" : "justify-content-start");

            if (tempId) messageDiv.dataset.tempId = tempId;
            if (dbId) messageDiv.dataset.messageId = dbId;

            const messageBubble = document.createElement("div");
            messageBubble.classList.add("p-3", "rounded-3", "shadow-sm");
            messageBubble.style.maxWidth = "75%";
            messageBubble.classList.add(isOwnMessage ? "bg-primary" : "bg-light", isOwnMessage ? "text-white" : "text-dark");

            if (tempId && !dbId) { // If it's an optimistic message not yet confirmed
                messageBubble.classList.add('optimistic-message');
                // Optionally add a pending indicator inside the bubble
                const pendingSpan = document.createElement('small');
                pendingSpan.className = 'pending-indicator fst-italic ms-1';
                pendingSpan.textContent = '(sending...)';
                // Append later
            }

            const displayName = isOwnMessage ? "You" : escapeHtml(senderUsername);

            let timeString = 'Sending...'; // Default for optimistic messages
            if (isoTimestamp) { // If timestamp is provided (i.e., from server)
                const dateObj = new Date(isoTimestamp);
                timeString = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } else if (!tempId) { // Fallback for non-optimistic messages without server timestamp (should not happen with new flow)
                 timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }


            messageBubble.innerHTML = `
                <p class="mb-1"><strong>${displayName}:</strong> ${escapeHtml(messageContent)}</p>
                <small class="${isOwnMessage ? 'text-light' : 'text-muted'}">${timeString}</small>
            `;

            if (tempId && !dbId && messageBubble.querySelector('small')) {
                const pendingSpan = document.createElement('small');
                pendingSpan.className = 'pending-indicator fst-italic ms-1 ' + (isOwnMessage ? 'text-light' : 'text-muted');
                pendingSpan.textContent = '(sending...)';
                messageBubble.querySelector('small').appendChild(pendingSpan);
            }


            messageDiv.appendChild(messageBubble);
            messageContainer.appendChild(messageDiv);
            
            scrollToBottom();
        }

        function escapeHtml(text) {
            if (typeof text !== 'string') return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function scrollToBottom() {
            if (messageContainer) {
                setTimeout(() => { // Ensure DOM update before scrolling
                    messageContainer.scrollTop = messageContainer.scrollHeight;
                }, 10);
            }
        }

        // Initial scroll to bottom when page loads (after existing messages are rendered)
        scrollToBottom();

        function showError(messageText, tempIdForFailedMessage = null) {
            // If a tempId is provided, try to mark that specific message as failed.
            if (tempIdForFailedMessage) {
                const failedMsgElement = document.querySelector(`[data-temp-id="${tempIdForFailedMessage}"]`);
                if (failedMsgElement) {
                    failedMsgElement.classList.add('message-error'); // Style for error
                    const errorIndicator = document.createElement('span');
                    errorIndicator.className = 'text-danger ms-1';
                    errorIndicator.textContent = '(Failed to send)';

                    const timeSmall = failedMsgElement.querySelector('small');
                    if(timeSmall) timeSmall.appendChild(errorIndicator);
                    else failedMsgElement.appendChild(errorIndicator);

                    return; // Don't show a generic error if we marked the specific message
                }
            }

            // Generic error display if no specific message to mark or element not found
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger alert-dismissible fade show mt-2';
            errorDiv.setAttribute('role', 'alert');
            errorDiv.innerHTML = `
                ${escapeHtml(messageText)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            const container = document.querySelector('.container.py-4'); // More specific container
            if (container && messageForm) { // Insert before the form
                messageForm.parentNode.insertBefore(errorDiv, messageForm);
            } else if (container) { // Fallback if form not found
                container.insertBefore(errorDiv, container.firstChild);
            } else { // Absolute fallback
                document.body.insertBefore(errorDiv, document.body.firstChild);
            }
        }

        // Handle form submission for sending messages
        if (messageForm) {
            messageForm.addEventListener('submit', async function(e) {
                e.preventDefault(); // Prevent traditional form submission
                
                const messageContent = messageInput.value.trim();
                if (!messageContent) return; // Do nothing if message is empty

                if (!isConnected || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) {
                    showError('Not connected. Cannot send message.');
                    return;
                }

                const tempId = generateTempId();

                // 1. Optimistic UI update: Display message immediately for the sender
                displayMessage(messageContent, username, true, null, null, tempId);

                const originalMessageValue = messageInput.value; // Store before clearing
                messageInput.value = ''; // Clear input field

                // 2. Send message via WebSocket
                try {
                    chatSocket.send(JSON.stringify({
                        type: 'chat_message', // New type for consumer
                        message: messageContent,
                        temp_id: tempId // Send temp_id for server to echo back
                        // Username is not needed here, server will get it from scope
                    }));
                } catch (error) {
                    console.error('Error sending message via WebSocket:', error);
                    showError('Failed to send message. Please check your connection.', tempId);
                    // Restore input if send fails immediately
                    messageInput.value = originalMessageValue;
                    // Optionally remove the optimistic message or mark as failed
                    const optimisticMsg = document.querySelector(`[data-temp-id="${tempId}"]`);
                    if(optimisticMsg) {
                         updateOptimisticMessage(optimisticMsg, { id: null}); // Mark as failed state
                         showError('Failed to send.', tempId);
                    }
                }
            });
        }

        // Handle typing indicators
        let typingTimeout;
        if (messageInput) {
            messageInput.addEventListener('input', function() {
                if (chatSocket && isConnected) {
                    chatSocket.send(JSON.stringify({
                        type: 'typing', // New type for consumer
                        typing: true
                        // Username from scope on server
                    }));

                    clearTimeout(typingTimeout);
                    typingTimeout = setTimeout(() => {
                        if (chatSocket && isConnected) {
                            chatSocket.send(JSON.stringify({
                                type: 'typing',
                                typing: false
                            }));
                        }
                    }, 1500); // User considered stopped typing after 1.5s
                }
            });
        }

        // Initialize WebSocket connection when everything is set up
        connectWebSocket();

        // Add connection status indicator to the page (optional)
        const statusDiv = document.createElement('div');
        statusDiv.id = 'connection-status';
        // Initial status (will be updated by connectWebSocket)
        statusDiv.className = 'text-danger small mb-2';
        statusDiv.textContent = '🔴 Disconnected';
        if (messageForm) { // Insert it before the message form
            messageForm.parentNode.insertBefore(statusDiv, messageForm);
        }

        // Cleanly close WebSocket on page unload
        window.addEventListener('beforeunload', function() {
            if (chatSocket) {
                chatSocket.close(1000, 'Page unload or navigation'); // Normal closure
            }
        });
    }
});