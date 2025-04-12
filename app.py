from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from datetime import datetime


# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='Templates')
CORS(app)  # Allow all origins for all routes

# Together API settings
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Dictionary to store user chat history
user_chat_history = {}

# List of professional mental health questions
mental_health_questions = [
    "On a scale of 1 to 10, how would you rate your overall mood today?",
    "Have you been experiencing frequent stress or anxiety in the past week?",
    "Are you having trouble sleeping or experiencing changes in your sleep pattern?",
    "Do you feel socially connected, or are you feeling isolated?",
    "Have you noticed any significant changes in your appetite or weight?",
    "Are you experiencing difficulty concentrating or making decisions?",
    "Do you often feel fatigued or low on energy throughout the day?",
    "Have you lost interest in activities that you used to enjoy?",
    "Do you feel overwhelmed by responsibilities in your personal or professional life?",
    "Are you currently facing any major life changes or stressful events?",
    "Have you had thoughts of self-harm or felt hopeless recently?",
    "Would you like any resources or guidance on coping strategies for mental well-being?"
]

def validate_together_api_key():
    """Validate the Together API key before making requests."""
    if not TOGETHER_API_KEY:
        raise ValueError("Together API key is not configured")
    if len(TOGETHER_API_KEY) != 64:  # Basic format check
        raise ValueError("Invalid Together API key format")

def analyze_responses_with_together(conversation_history, assessment_mode=False, answers=None):
    """
    Send conversation history or assessment answers to the Together API for analysis.
    
    Args:
        conversation_history (list): List of messages for general conversation.
        assessment_mode (bool): If True, analyze assessment answers.
        answers (list): List of user answers for assessment (required if assessment_mode is True).
    
    Returns:
        str: API response content or error message
    """
    try:
        validate_together_api_key()
        
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }

        if assessment_mode:
            if not answers or len(answers) != len(mental_health_questions):
                raise ValueError("Invalid assessment answers provided")
                
            messages = [{
                "role": "system",
                "content": (
                    "You are a mental health assistant. Analyze the user's answers to the assessment questions and provide:\n"
                    "1. A structured summary of key findings\n"
                    "2. Identified patterns or concerns\n"
                    "3. Actionable advice\n"
                    "Use markdown formatting for clarity.\n"
                    "### Guidelines:\n"
                    "- *Structured Responses:* Format responses clearly using bullet points, numbered lists, and line breaks\n"
                    "- *Bold text* for emphasis\n"
                    "- Bullet points (•) for lists\n"
                    "- Numbered lists (1., 2.) where appropriate\n"
                    "- Line breaks (\\n) for readability\n"
                    "- Maintain a warm, professional, and non-judgmental tone"
                )
            }]

            for i, answer in enumerate(answers):
                messages.append({
                    "role": "user",
                    "content": f"Question {i + 1}: {mental_health_questions[i]}\nAnswer: {answer}"
                })
        else:
            if not conversation_history:
                raise ValueError("Empty conversation history")
            messages = conversation_history

        data = {
            "model": "mistralai/Mistral-7B-Instruct-v0.1",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }

        response = requests.post(TOGETHER_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if not result.get("choices"):
            raise ValueError("Unexpected API response format")
            
        return result["choices"][0]["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        return f"⚠️ Service temporarily unavailable. Please try again later. (Error: {str(e)})"
    except ValueError as e:
        return f"⚠️ Validation error: {str(e)}"
    except Exception as e:
        return f"⚠️ An unexpected error occurred: {str(e)}"
    
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle chat requests from the frontend, storing user chat history.
    """
    data = request.json
    user_name = data.get("username", "guest")  # Default username if not provided
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please enter a valid message.", "status": "error"}), 400

    # Retrieve user's chat history, or start a new one
    if user_name not in user_chat_history:
        user_chat_history[user_name] = []

    # Append new user message
    user_chat_history[user_name].append({"role": "user", "content": user_message})

    # Check if the user is in an assessment
    if user_name in user_assessment_state:
        assessment_state = user_assessment_state[user_name]
        current_question_index = assessment_state["current_question_index"]
        answers = assessment_state["answers"]

        # Store the user's answer
        answers.append(user_message)

        # Check if all questions have been answered
        if current_question_index + 1 < len(mental_health_questions):
            # Ask the next question
            next_question_index = current_question_index + 1
            user_assessment_state[user_name]["current_question_index"] = next_question_index

            return jsonify({
                'reply': mental_health_questions[next_question_index],
                'status': 'assessment'
            })
        else:
            # All questions answered, provide a summary or analysis
            analysis = analyze_responses_with_together(
                conversation_history=None,  # No general conversation history
                assessment_mode=True,       # Enable assessment mode
                answers=answers             # Pass user answers
            )
            del user_assessment_state[user_name]  # Clear assessment state

            return jsonify({
                'reply': analysis,
                'status': 'analysis'
            })
    else:
        # Always include system instructions for general chat
        system_message = {        
            "role": "system",
            "content": 
                "You are a professional mental health assistant. Provide empathetic, supportive responses based on the user's input.\n"
                "Offer coping strategies and insights without asking structured questions.\n"
                "Maintain a warm, conversational tone. Use markdown formatting for clarity when needed.\n"
                "### Guidelines:\n"
                "- *Structured Responses:* Format responses clearly using bullet points, numbered lists, and line breaks\n"
                "- *Bold text* for emphasis\n"
                "- Bullet points (•) for lists\n"
                "- Numbered lists (1., 2.) where appropriate\n"
                "- Line breaks (\\n) for readability\n"
                "- Maintain a warm, professional, and non-judgmental tone"
        }
        
        conversation_history = [system_message] + user_chat_history[user_name]

        # Get AI-generated response
        bot_reply = analyze_responses_with_together(conversation_history)

        # Append bot response to user history
        user_chat_history[user_name].append({"role": "assistant", "content": bot_reply})

        # Ensure we always return a properly formatted response
        if not bot_reply:
            bot_reply = "I'm sorry, I didn't get a response. Please try again."
            
        return jsonify({
            'status': 'success',
            'reply': bot_reply,
            'question': None,  # Explicitly set question to null for non-assessment responses
            'formatted_reply': f"""
                <div class='chat-response'>
                    <p class='response-text'>{bot_reply}</p>
                    <p class='response-meta'>Response generated at: {datetime.now().strftime('%H:%M')}</p>
                </div>
            """,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'response_type': 'text',
                'history_length': len(user_chat_history[user_name])
            }
        })

# Dictionary to store user assessment state
user_assessment_state = {}

@app.route('/api/start_assessment', methods=['POST', 'OPTIONS'])
def start_assessment():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    data = request.json
    user_name = data.get("username", "guest")

    # Clear any existing assessment state for this user
    if user_name in user_assessment_state:
        del user_assessment_state[user_name]

    # Initialize fresh assessment state for the user
    user_assessment_state[user_name] = {
        "current_question_index": 0,
        "answers": []
    }
    
    # Start the assessment with the first question
    return jsonify({
        'reply': "Starting your mental health assessment. First question:",
        'question': mental_health_questions[0],
        'status': 'assessment'
    })

@app.route('/api/get_history', methods=['POST'])
def get_chat_history():
    """
    Retrieve user chat history.
    """
    data = request.json
    user_name = data.get("username", "guest")
    history = user_chat_history.get(user_name, [])
    return jsonify({'history': history})

@app.route('/api/clear_history', methods=['POST'])
def clear_chat_history():
    """Clear user chat history"""
    data = request.json
    user_name = data.get("username", "guest")
    
    if user_name in user_chat_history:
        del user_chat_history[user_name]
    
    return jsonify({
        "status": "success",
        "message": "Chat history cleared"
    })

@app.route('/api/clear_assessment', methods=['POST'])
def clear_assessment_state():
    """Clear user assessment state"""
    data = request.json
    user_name = data.get("username", "guest")
    
    if user_name in user_assessment_state:
        del user_assessment_state[user_name]
    
    return jsonify({
        "status": "success",
        "message": "Assessment state cleared"
    })

@app.route('/api/track_mood', methods=['POST'])
def track_mood():
    """
    Track and store user mood data.
    """
    data = request.json
    mood = data.get("mood", "").lower()
    username = data.get("username", "guest")
    
    if not mood or mood not in ["happy", "sad", "anxious"]:
        return jsonify({"status": "error", "message": "Invalid mood value"}), 400
    
    # In a real app, you would store this in a database
    print(f"User {username} reported feeling {mood}")  # Log for demonstration
    
    return jsonify({
        "status": "success",
        "message": f"Mood '{mood}' recorded",
        "suggestion": get_mood_suggestion(mood)
    })

def get_mood_suggestion(mood):
    """Return appropriate suggestions based on mood"""
    suggestions = {
        "happy": "Great to hear you're feeling happy! Consider journaling about what's making you happy.",
        "sad": "It's okay to feel sad sometimes. You might try calling a friend or going for a walk.",
        "anxious": "For anxiety, try deep breathing exercises or mindfulness techniques."
    }
    return suggestions.get(mood, "Thank you for sharing how you're feeling.")

from flask import send_from_directory, render_template

@app.route('/')
def index():
    """Serve the main frontend interface"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error rendering template: {str(e)}"

@app.route('/api')
def api_info():
    """Provide API information"""
    return jsonify({
        'status': 'running',
        'endpoints': {
            '/api/chat': 'POST - Handle chat messages',
            '/api/start_assessment': 'POST - Start mental health assessment',
            '/api/get_history': 'POST - Get chat history'
        }
    })

# Static file serving
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)