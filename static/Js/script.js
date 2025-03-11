// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const emergencyBtn = document.getElementById('emergency-btn');
const startAssessmentBtn = document.getElementById('start-assessment-btn'); // New Button
const usernameModal = document.getElementById('username-modal');
const usernameInput = document.getElementById('username-input');
const saveUsernameBtn = document.getElementById('save-username-btn');

// Determine the backend URL based on the environment
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const BACKEND_URL = isLocal ? 'http://127.0.0.1:5000' : 'https://mentalyze-backend.onrender.com';

let username = localStorage.getItem('username') || 'guest';
let isUserScrolling = false;  // Flag to track manual scrolling

document.addEventListener("DOMContentLoaded", function () {
  // Add click event listeners to navbar links
  const links = document.querySelectorAll(".nav-link");
  const sections = document.querySelectorAll(".section");
  const navbarToggler = document.querySelector(".navbar-toggler");
  const navbarCollapse = document.querySelector(".navbar-collapse");

  // Hide all sections by default except the Home section
  sections.forEach(section => section.style.display = "none");
  document.getElementById("Home").style.display = "block"; // Display Home section by default

  links.forEach(link => {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      // Get the target section
      const targetId = this.getAttribute("href").substring(1);
      const targetSection = document.getElementById(targetId);

      // Hide all sections and then display the target section
      sections.forEach(section => section.style.display = "none");
      targetSection.style.display = "block";

      // Optionally, you can highlight the clicked link
      links.forEach(link => link.classList.remove("active"));
      this.classList.add("active");

      // Close the navbar after clicking a link
      if (navbarCollapse.classList.contains("show")) {
        navbarToggler.click();
      }
    });
  });

  document.addEventListener("click", function(event) {
    const resetButton = document.getElementById("resetBtn");
    if (event.target === resetButton) {
      window.location.reload();
    }
  });
  
  
  // Close navbar when clicking outside of it
  document.addEventListener("click", function (event) {
    const isClickInsideNavbar = navbarToggler.contains(event.target) || navbarCollapse.contains(event.target);
    if (!isClickInsideNavbar && navbarCollapse.classList.contains("show")) {
      navbarToggler.click();
    }
  });
});


// Function to add a message to the chat window
function addMessage(role, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', role);
    
    // Convert Markdown-style text to HTML (basic handling for bold and line breaks)
    message = message.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
  
    // Start with an empty message
    const strongTag = `<strong>${role}:</strong> `;
    messageElement.innerHTML = `<strong>${role}:</strong> ${message}`;
    chatMessages.appendChild(messageElement);
    
    // Simulate typing effect (print text gradually)
    let i = 0;
    function typeCharacter() {
      
      if (i < message.length) {
        messageElement.innerHTML = strongTag + message.substring(0, i + 1);
        i++;
        setTimeout(typeCharacter, 10);  // Adjust typing speed here
      }
      // Auto-scroll to the bottom only if the user is not manually scrolling
      if (!isUserScrolling) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    }
    
    // Ensure smooth scrolling to the bottom of the chat
    typeCharacter();
    setTimeout(() => {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
  }
  
  
  // Function to send a message to the backend (Flask server)
  async function sendMessage(message) {
    if (!message) return;
    addMessage('You', message);
  
    try {
      console.log("Sending message to backend:", message);
  
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
  
      if (!response.ok) {
        throw new Error(`Server error: ${response.status} - ${response.statusText}`);
      }
  
      const data = await response.json();
      console.log("Received response from backend:", data);
  
      // Directly display the chatbot's response without unnecessary status checks
      addMessage('Mentalyze', data.reply);
    } catch (error) {
      console.error('Error:', error);
      addMessage('Mentalyze', '⚠️ Error communicating with the server. Please try again later.');
    }
  }
  
  
  // Function to start assessment
  async function startAssessment() {
    addMessage('You', 'Starting assessment...');
  
    try {
      const response = await fetch(`${BACKEND_URL}/api/start_assessment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
  
      if (!response.ok) throw new Error(`Server error: ${response.status} - ${response.statusText}`);
  
      const data = await response.json();
      addMessage('Mentalyze', `${data.reply} <br><strong>${data.question}</strong>`);
    } catch (error) {
      console.error('Error:', error);
      addMessage('Mentalyze', '⚠️ Error starting the assessment. Please try again.');
    }
  }
  
  startAssessmentBtn.addEventListener('click', startAssessment);
  
  
  // Clear chat on refresh
  window.onload = function () {
    document.getElementById("chat-messages").innerHTML = "";
    askForUsername();
    getChatHistory();  // Load chat history on page load
  };
  
  // Function to send emergency alert
  function sendEmergencyAlert() {
    alert('Emergency alert triggered! Please contact a trusted person or helpline.');
  }
  
  // Event listener for manual scrolling
  chatMessages.addEventListener('scroll', () => {
    // Check if the user is scrolling up
    const scrollTop = chatMessages.scrollTop;
    const scrollHeight = chatMessages.scrollHeight;
    const clientHeight = chatMessages.clientHeight;
  
    // If the user is not at the bottom, set the flag to true
    if (scrollTop + clientHeight < scrollHeight - 10) {  // 10px buffer
      isUserScrolling = true;
    } else {
      isUserScrolling = false;
    }
  });
  
  // Event Listeners
  sendBtn.addEventListener('click', () => {
    const message = chatInput.value.trim();
    sendMessage(message);
    chatInput.value = '';
  });
  
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const message = chatInput.value.trim();
      sendMessage(message);
      chatInput.value = '';
    }
  });
  
  emergencyBtn.addEventListener('click', sendEmergencyAlert);
  
  document.querySelectorAll('.navbar-nav a').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href').substring(1);
      document.getElementById(targetId).scrollIntoView({
        behavior: 'smooth'
      });
    });
  });