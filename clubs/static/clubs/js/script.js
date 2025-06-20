document.addEventListener("DOMContentLoaded", function () {
  console.log("School Club Management System loaded.");

  // Auto-scroll the chat box to the bottom if it exists
  const chatBox = document.querySelector(".chat-box");
  if (chatBox) {
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // Optional: Enhance alert dismissal with a fade-out effect (Bootstrap 5 handles this natively)
  document.querySelectorAll('.alert').forEach(alert => {
    alert.addEventListener('close.bs.alert', function () {
      // Add any custom behavior here if needed
      console.log("Alert closed");
    });
  });

  // Additional interactive features can be added here
  // For example: Toggle dark mode, load notifications dynamically, etc.
});
