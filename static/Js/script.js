// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const emergencyBtn = document.getElementById('emergency-btn');
const startAssessmentBtn = document.getElementById('start-assessment-btn');
const loadingSpinner = document.getElementById('loading-spinner');
const happyBtn = document.getElementById('happy-btn');
const sadBtn = document.getElementById('sad-btn');
const anxiousBtn = document.getElementById('anxious-btn');
const confirmEmergencyBtn = document.getElementById('confirmEmergency');
const voiceBtn = document.getElementById('voice-btn');

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

  // Mood button event listeners
  happyBtn.addEventListener('click', () => trackMood('happy'));
  sadBtn.addEventListener('click', () => trackMood('sad'));
  anxiousBtn.addEventListener('click', () => trackMood('anxious'));
  confirmEmergencyBtn.addEventListener('click', sendEmergencyAlert);
  
  // Voice button event listener
  if (voiceBtn) {
    voiceBtn.addEventListener('click', startVoiceRecognition);
  }
});

// Voice recognition function
function startVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        addMessage('Mentalyze', '⚠️ Voice recognition is not supported in your browser.');
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();
    addMessage('Mentalyze', 'Listening... Speak now');

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        sendMessage(transcript);
        chatInput.value = ''; // Clear input after sending
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        addMessage('Mentalyze', '⚠️ Error recognizing speech. Please try again.');
    };

    recognition.onend = () => {
        // Recognition ended
    };
}

// Function to add a message to the chat window
function addMessage(role, message) {
    if (!message) {
        console.error('Attempted to add empty message');
        return;
    }
    
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', role);
    
    // Ensure message is a string before processing
    const processedMessage = String(message)
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
        
    messageElement.innerHTML = `<strong>${role}:</strong> ${processedMessage}`;
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

// Function to send a message to the backend (Flask server)
async function sendMessage(message) {
    if (!message) return;
    addMessage('You', message);
    loadingSpinner.style.display = 'block';
    sendBtn.disabled = true;

    try {
      // First check if backend is reachable
      const pingResponse = await fetch(`${BACKEND_URL}/api`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!pingResponse.ok) {
        throw new Error('Backend service unavailable');
      }

      // If ping successful, send the chat message
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();
      addMessage('Mentalyze', data.reply);
    } catch (error) {
      console.error('Error:', error);
      let errorMsg = '⚠️ Error communicating with the server. ';
      
      if (error.message.includes('Failed to fetch') || error.message.includes('Backend service unavailable')) {
        errorMsg += 'Please ensure the backend service is running.';
        if (isLocal) {
          errorMsg += ' Try: "flask run" in your terminal.';
        }
      } else {
        errorMsg += 'Please try again later.';
      }
      
      addMessage('Mentalyze', errorMsg);
    } finally {
      loadingSpinner.style.display = 'none';
      sendBtn.disabled = false;
    }
}

// Track user's mood
async function trackMood(mood) {
    addMessage('You', `I'm feeling ${mood}`);
    // Highlight selected mood button
    document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline-primary');
    });
    event.target.classList.add('btn-primary');
    event.target.classList.remove('btn-outline-primary');
    
    try {
        // Send mood to backend
        const response = await fetch(`${BACKEND_URL}/api/track_mood`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mood, username })
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const data = await response.json();
        addMessage('Mentalyze', `${data.message}. ${data.suggestion}`);
    } catch (error) {
        console.error('Error:', error);
        addMessage('Mentalyze', '⚠️ Error tracking mood. Please try again.');
    }
}

let isAssessmentActive = false;

// Function to start assessment
async function startAssessment() {
    try {
        loadingSpinner.style.display = 'block';
        startAssessmentBtn.disabled = true;

        const response = await fetch(`${BACKEND_URL}/api/start_assessment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const data = await response.json();
        isAssessmentActive = true;
        addMessage('Mentalyze', data.reply + "<br><br><strong>" + data.question + "</strong>");
    } catch (error) {
        console.error('Error:', error);
        addMessage('Mentalyze', '⚠️ Error starting assessment. Please try again later.');
    } finally {
        loadingSpinner.style.display = 'none';
        startAssessmentBtn.disabled = false;
    }
}

// Modified sendMessage function to handle assessment flow
async function sendMessage(message) {
    if (!message) return;
    addMessage('You', message);
    loadingSpinner.style.display = 'block';
    sendBtn.disabled = true;

    try {
        if (isAssessmentActive) {
            // Check if user wants to stop assessment
            if (message.toLowerCase().includes('stop assessment')) {
                isAssessmentActive = false;
                addMessage('Mentalyze', 'Assessment stopped. How can I help you?');
                return;
            }

            // Send message to chat endpoint which handles assessment flow
            const response = await fetch(`${BACKEND_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message,
                    username
                })
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            
            if (data.status === 'assessment') {
                // Continue with next assessment question
                const question = data.question || "Please share more about how you're feeling";
                addMessage('Mentalyze', data.reply + "<br><br><strong>" + question + "</strong>");
            } else if (data.status === 'analysis') {
                // Assessment complete
                isAssessmentActive = false;
                addMessage('Mentalyze', data.reply + "<br><br>Assessment complete. How else can I help?");
            } else {
                // Regular chat response
                addMessage('Mentalyze', data.reply);
            }
        } else {
            // Normal chat flow
            const response = await fetch(`${BACKEND_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            addMessage('Mentalyze', data.reply);
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('Mentalyze', '⚠️ Error processing your message. Please try again.');
    } finally {
        loadingSpinner.style.display = 'none';
        sendBtn.disabled = false;
    }
}

startAssessmentBtn.addEventListener('click', startAssessment);

// Clear chat on refresh
window.onload = function () {
    document.getElementById("chat-messages").innerHTML = "";
};

// Function to send emergency alert
function sendEmergencyAlert() {
    // This is now handled by the modal confirmation
    fetch(`${BACKEND_URL}/api/emergency`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
        if (!response.ok) throw new Error('Emergency alert failed');
        addMessage('Mentalyze', 'Emergency support has been notified. Help is on the way.');
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('Mentalyze', '⚠️ Emergency alert failed. Please call for help directly.');
    });
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

// Auto-scroll to bottom when new messages arrive
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

document.querySelectorAll('.navbar-nav a').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href').substring(1);
      document.getElementById(targetId).scrollIntoView({
        behavior: 'smooth'
      });
    });
});
