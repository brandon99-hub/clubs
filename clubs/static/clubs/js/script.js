document.addEventListener("DOMContentLoaded", function () {
    console.log("School Club Management System loaded.");

    // Auto-scroll the chat box to the bottom if it exists
    const chatBox = document.querySelector(".chat-box");
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Dark Mode Toggle Logic
    const darkModeToggle = document.getElementById("darkModeToggle");
    const currentTheme = localStorage.getItem("theme");
    if (currentTheme === "dark") {
        document.body.classList.add("dark-mode");
        const navbar = document.querySelector("nav.navbar");
        if (navbar) {
            navbar.classList.add("dark-mode");
        }
    }

    darkModeToggle?.addEventListener("click", function () {
        document.body.classList.toggle("dark-mode");
        const navbar = document.querySelector("nav.navbar");
        if (navbar) {
            navbar.classList.toggle("dark-mode");
        }
        localStorage.setItem("theme", document.body.classList.contains("dark-mode") ? "dark" : "light");
    });

    // WebSocket Chat Logic
    if (!roomName) {
        console.error("Room name is missing! WebSocket connection aborted.");
    } else {
        const chatSocket = new WebSocket(
            'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
        );

        chatSocket.onerror = function (e) {
            console.error("WebSocket error occurred:", e);
            alert("Chat server error. Please try again later.");
        };

        chatSocket.onclose = function (e) {
            console.error("Chat socket closed unexpectedly. Code:", e.code, "Reason:", e.reason);
        };

        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            console.log("WebSocket data received:", data); // Helps you debug the data received

            const messageContainer = document.getElementById('chat-area');
            const typingIndicator = document.getElementById('typing-indicator');

            // Update typing indicator
            if ("typing" in data) {
                if (data.typing && data.username !== username) {
                    typingIndicator.textContent = `${data.username} is typing...`;
                } else {
                    typingIndicator.textContent = ""; // Clear typing indicator when typing stops
                }
            }

            // Handle only chat messages, ignore everything else
            if ("message" in data) {
                const messageDiv = document.createElement("div");
                messageDiv.classList.add(
                    "chat-message",
                    data.username === username ? "text-end" : "text-start",
                    "mb-3"
                );

                messageDiv.innerHTML = `
            <div class="${data.username === username ? "bg-primary text-white" : "bg-light text-dark"} p-2 rounded">
                <p class="mb-1"><strong>${data.username === username ? "You" : data.username}:</strong> ${data.message}</p>
            </div>
        `;

                // Append the message to the chat area and auto-scroll to the bottom
                messageContainer.appendChild(messageDiv);
                messageContainer.scrollTop = messageContainer.scrollHeight;
            } else {
                // Skip any data that isn't a recognized type
                console.log("Unprocessed data ignored:", data);
            }
        };
    }
});