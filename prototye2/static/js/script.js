document.addEventListener("DOMContentLoaded", function () {
console.log("program")
// document.getElementById('login-form')?.addEventListener('submit', (e) => {
//     e.preventDefault();
//     alert('Login submitted!');
// });

document.getElementById('signup-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Sign-Up submitted!');
});

document.getElementById('forgot-password-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Password reset instructions sent to your email!');
});
// Select the login form

//const loginForm = document.getElementById('login-form');
// const loginForm = document.getElementById('login-form');

// Handle form submission
// if (loginForm) {

    // loginForm.addEventListener('submit', (e) => {
    //     e.preventDefault(); // Prevent default form submission

        // Get form values (optional validation)
        // const email = document.getElementById('email').value.trim();
        // const password = document.getElementById('password').value.trim();

        // if (email && password) {
            // Optionally, validate credentials here or display a message
            // console.log("Email:", email);
            // console.log("Password:", password);

            // Redirect to the chat page
            // const chatUrl = loginForm.getAttribute('data-chat-url');
            // window.location.href = "{{ url_for('chat') }}";
            // window.location.href = chatUrl;

//         } else {
//             alert('Please fill in all required fields.');
//         }
//     });
// }

// Redirect to the chat page upon login form submission
// document.getElementById('login-form').addEventListener('submit', (e) => {
//     e.preventDefault(); // Prevent form submission
//     window.location.href = 'index.html'; // Redirect to chat page
// });
let countdown = 120; // 30 seconds countdown
    // let timerElement = document.getElementById("timer");
    let resendButton = document.getElementById("resend-button");
    let timerElement = document.getElementById("timer-text");
    let resendLink = document.getElementById("resend-link");
    let otpInputField = document.getElementById("otp");

    function updateTimer() {
        // console.log("Countdown is: " + countdown);
        if (countdown > 0) {
            countdown--;
            timerElement.textContent = countdown; // Update countdown timer
            setTimeout(updateTimer, 1000);
        } else {
            // Show the "Resend OTP" link after countdown finishes
            resendLink.style.display = "inline";
            timerElement.style.display = "none"; // Hide countdown timer
        }
    }

    

    window.onload = function() {
        // Check if we are on the verify page
        if (window.location.pathname.includes("verify")) {
            updateTimer(); // Call the updateTimer function only on verify.html
        }
    };
});