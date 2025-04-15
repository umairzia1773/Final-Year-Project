document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed"); // Debugging
    
    setTimeout(() => {
        // Select all flash alerts using the common class (e.g., .alert)
        const alerts = document.querySelectorAll(".alert");
        alerts.forEach((alert) => {
          // Add a fade-out transition
          alert.style.transition = "opacity 0.5s ease-out";
          alert.style.opacity = "0";
          // After the fade-out transition (500ms), remove the element
          setTimeout(() => {
            alert.style.display = "none";
          }, 1000);
        });
      }, 6000);
    
    // CAPTCHA State
    let isCaptchaValid = false;
    let captchaToken = null;
    let captchaRendered = false;
    let captchaWidgetId = null;
    window.onRecaptchaLoad = function() {
        renderCaptcha();
    };
    // DOM Elements
    const passwordRulesBox = document.getElementById('password-rules-box');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const confirmPasswordError = document.getElementById('confirm-password-error');
    const signupForm = document.getElementById('signup-form');
    const captchaError = document.getElementById('captcha-error');

    
    // CAPTCHA Success Handler
    window.onCaptchaSuccess = function (token) {
        console.log("CAPTCHA solved successfully! Token:", token); // Debugging
        isCaptchaValid = true;
        captchaToken = token;
        captchaError.style.display = 'none';
    };
    
    // In the renderCaptcha function, use the same site key
    function renderCaptcha() {
        if (!captchaRendered && window.grecaptcha) {
            const captchaElement = document.querySelector('.g-recaptcha');
            if (captchaElement) {
                captchaWidgetId = grecaptcha.render(captchaElement, {
                    sitekey: '6LdhBOcqAAAAAN1ZJhz9tMEqz9cDbGsZ3-Kh6CAo',
                    callback: onCaptchaSuccess
                });
                captchaRendered = true;
            } else {
                console.error("No element found with class 'g-recaptcha'");
            }
        }
    }
    // renderCaptcha();
    
    

    // Password Rules Validation
    if (passwordInput && passwordRulesBox) {
        passwordInput.addEventListener('focus', () => {
            console.log("Password input focused"); // Debugging
            passwordRulesBox.style.display = 'block';
        });

        passwordInput.addEventListener('blur', () => {
            console.log("Password input blurred"); // Debugging
            passwordRulesBox.style.display = 'none';
        });

        passwordInput.addEventListener('input', () => {
            const password = passwordInput.value;

            // Check length
            const lengthValid = password.length >= 8;
            document.getElementById('length').classList.toggle('valid', lengthValid);

            // Check for at least 1 uppercase and lowercase letter
            const lettersValid = /[a-z]/.test(password) && /[A-Z]/.test(password);
            document.getElementById('letters').classList.toggle('valid', lettersValid);

            // Check for at least 1 number and 1 special character
            const numbersSpecialValid = /\d/.test(password) && /[@$!%*?&]/.test(password);
            document.getElementById('numbers-special').classList.toggle('valid', numbersSpecialValid);

            // Hide the box if all rules are met
            if (lengthValid && lettersValid && numbersSpecialValid) {
                passwordRulesBox.style.display = 'none';
            }
        });
    } else {
        console.error("Password input or rules box not found!"); // Debugging
    }

    // Toggle Password Visibility
    window.togglePasswordVisibility = function (fieldId, button) {
        const field = document.getElementById(fieldId);
        if (!field) {
            console.error(`Field with ID ${fieldId} not found.`);
            return;
        }
    
        // Get the slash line from the SVG inside the button
        const slash = button.querySelector('#slash');
    
        if (field.type === "password") {
            // Show password
            field.type = "text";
            button.setAttribute('aria-label', 'Hide password');
            
            // Show the slash line
            if (slash) {
                slash.style.display = 'block';
            }
        } else {
            // Hide password
            field.type = "password";
            button.setAttribute('aria-label', 'Show password');
            
            // Hide the slash line
            if (slash) {
                slash.style.display = 'none';
            }
        }
    };

    
    
    // Form Submission Handler
    if (signupForm) {
        signupForm.addEventListener('submit', function (e)  {
            // e.preventDefault();
            console.log("Form submission started");
            const submitButton = signupForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
            }
            // // Stop session check while submitting the form
            // stopSessionCheck();

           
            // captchaError.style.display = 'none';
            document.getElementById('captcha-error').style.display = 'none';
            confirmPasswordError.style.display = 'none';
            captchaError.style.display = 'none';

             // Reset 
             let isValid = true;

            // Password validation
            // const password = passwordInput.value;
            // const confirmPassword = confirmPasswordInput.value;
            // if (password !== confirmPassword) {
            //     confirmPasswordError.textContent = 'Passwords do not match';
            //     confirmPasswordError.style.display = 'block';
            //     isValid = false;
            // } else {
            //     confirmPasswordError.style.display = 'none'; // Clear error if matched
            // }

            

            // CAPTCHA validation
            const googleCaptchaToken = grecaptcha.getResponse();
            console.log("Google CAPTCHA token:", googleCaptchaToken);
            if (googleCaptchaToken === "") {
            captchaError.textContent = 'Please complete the CAPTCHA verification';
            captchaError.style.display = 'block';
            isValid = false;
            }
            // if (!isCaptchaValid || !captchaToken) {
            //     captchaError.textContent = 'Please complete the CAPTCHA verification';
            //     captchaError.style.display = 'block';
            //     isValid = false;
            //     resetCaptcha();
            // }
            if (!isValid) {
                console.log("Invalid form submission, resetting CAPTCHA...");
                resetCaptcha(); // Only reset if invalid
                e.preventDefault();
                if (submitButton) {
                    submitButton.disabled = false;
                }
                return;
            }
            
            

            // Server-side verification
            try {
                const formData = new FormData(signupForm);
                console.log("Submitting form with CAPTCHA token:", captchaToken);

                formData.append('g-recaptcha-response', googleCaptchaToken);

                // const response =  await fetch('/signup', {
                const response =   fetch('/signup', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                // const data = await response.json();
                const data = response.json();

                if (data.success) {
                    window.location.href = '/login'; // Redirect on success
                } else {
                    // Display server error (e.g., "Email already exists")
                    const passwordErrorDiv = document.getElementById('password-error');
                    passwordErrorDiv.textContent = data.message;
                    passwordErrorDiv.classList.add('error'); // Apply red styling
                    passwordErrorDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Error:', error);
            }
            // finally {
                
            //     // resetCaptcha();
            // }

        });
    }

    // Reset CAPTCHA
    function resetCaptcha() {
        isCaptchaValid = false;
        captchaToken = null;
        captchaRendered = false;
        if (window.grecaptcha) grecaptcha.reset();
    }

    // Session Check Logic
    function checkSession() {
        fetch('/check-session')
            .then(response => response.json())
            .then(data => {
                const publicPages = ['/login', '/signup', '/password', '/verify', '/reset-password'];
                if (!data.active && !publicPages.includes(window.location.pathname)) {
                    window.location.href = '/login';
                }
            })
            .catch(error => console.error('Error checking session:', error));
    }

    checkSession();
    
    

    // Public Pages (No Session Check Required)
    const currentPath = window.location.pathname;
    const publicPages = [
    '/login',
    '/signup',
    '/password',
    '/verify',
    '/reset-password'
    ];

// Only run session checks on pages that require authentication
if (!publicPages.includes(currentPath)) {
    setInterval(checkSession, 60000); // Check every minute
}

    // Timer Logic for OTP
    let countdown = 120; // 2 minutes countdown
    let timerElement = document.getElementById("timer-text");
    let resendLink = document.getElementById("resend-link");

    function updateTimer() {
        if (countdown > 0) {
            countdown--;
            if (timerElement) timerElement.textContent = countdown; // Update countdown timer
            setTimeout(updateTimer, 1000);
        } else {
            // Show the "Resend OTP" link after countdown finishes
            if (resendLink) resendLink.style.display = "inline";
            if (timerElement) timerElement.style.display = "none"; // Hide countdown timer
        }
    }

    // Call updateTimer only on the verify page
    if (window.location.pathname.includes("verify")) {
        updateTimer();
    }
});