document.addEventListener("DOMContentLoaded", function () {
    console.log("School Club Management System loaded.");

    // Sticky Navbar Scroll Effect
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Page Transition Management
    const pageContent = document.querySelector('.page-content');
    const loadingSpinner = document.querySelector('.loading-spinner');
    
    // Show loading spinner on page load
    if (loadingSpinner) {
        loadingSpinner.classList.add('show');
        setTimeout(() => {
            loadingSpinner.classList.remove('show');
        }, 800);
    }

    // Handle page transitions for internal links
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link && link.href && link.href.startsWith(window.location.origin) && !link.href.includes('#') && !link.target) {
            e.preventDefault();
            
            // Add exit animation
            if (pageContent) {
                pageContent.classList.add('page-exit');
            }
            
            // Show loading spinner
            if (loadingSpinner) {
                loadingSpinner.classList.add('show');
            }
            
            // Navigate after animation
            setTimeout(() => {
                window.location.href = link.href;
            }, 400);
        }
    });

    // Handle form submissions with transitions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.method === 'post' || form.method === 'POST') {
            // Show loading spinner
            if (loadingSpinner) {
                loadingSpinner.classList.add('show');
            }
        }
    });

    // Auto-scroll the chat box to the bottom if it exists
    const chatBox = document.querySelector(".chat-box");
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Enhanced Dark Mode Toggle Logic
    const darkModeToggle = document.getElementById("darkModeToggle");
    const currentTheme = localStorage.getItem("theme");
    
    // Initialize theme state
    if (currentTheme === "dark") {
        document.body.classList.add("dark-mode");
        const navbar = document.querySelector("nav.navbar");
        if (navbar) {
            navbar.classList.add("dark-mode");
        }
        // Set toggle to checked state
        if (darkModeToggle) {
            darkModeToggle.checked = true;
        }
    } else {
        // Set toggle to unchecked state
        if (darkModeToggle) {
            darkModeToggle.checked = false;
        }
    }

    // Enhanced toggle function with animations
    darkModeToggle?.addEventListener("change", function () {
        // Toggle dark mode
        const isDarkMode = this.checked;
        document.body.classList.toggle("dark-mode", isDarkMode);
        const navbar = document.querySelector("nav.navbar");
        if (navbar) {
            navbar.classList.toggle("dark-mode", isDarkMode);
        }
        
        // Update localStorage
        localStorage.setItem("theme", isDarkMode ? "dark" : "light");
        
        // Add a subtle animation effect
        this.parentElement.classList.add("toggle-animation");
        setTimeout(() => {
            this.parentElement.classList.remove("toggle-animation");
        }, 400);
    });

    // Enhanced Navigation Link Effects
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Enhanced Button Click Effects
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Enhanced Form Input Effects
    const formInputs = document.querySelectorAll('.form-control');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add ripple effect CSS dynamically
    const style = document.createElement('style');
    style.textContent = `
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});