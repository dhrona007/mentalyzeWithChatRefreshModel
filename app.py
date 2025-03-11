from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
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

def analyze_responses_with_together(conversation_history, assessment_mode=False, answers=None):
    """
    Send conversation history or assessment answers to the Together API for analysis.
    
    Args:
        conversation_history (list): List of messages for general conversation.
        assessment_mode (bool): If True, analyze assessment answers.
        answers (list): List of user answers for assessment (required if assessment_mode is True).
    """
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    if assessment_mode:
        # Prepare the conversation history for assessment analysis
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a mental health assistant. Analyze the user's answers to the assessment questions and provide a summary or analysis. "
                "Focus on identifying patterns, potential issues, and actionable advice. Keep the response structured and empathetic."
                )
            }
        ]

        # Add the user's answers to the conversation history
        for i, answer in enumerate(answers):
            messages.append({
                "role": "user",
                "content": f"Question {i + 1}: {mental_health_questions[i]}\nAnswer: {answer}"
            })
    else:
        # Use the provided conversation history for general chat
        messages = conversation_history

    data = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",
        "messages": messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(TOGETHER_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"❌ Error with Together API: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Error with Together API: {e}"
    
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
    else:# Always include system instructions
        system_message = {
        "role": "system",
        "content": 
                      "You are a highly professional mental health assistant. Your role is to provide structured, empathetic, and evidence-based psychological support. "
                "You are a mental health assistant. Your role is to provide empathetic and supportive responses to the user's inputs. \n\n"
        "Ask questions to understand the user's feelings and concerns, and provide helpful advice or coping strategies.\n\n"
        "Keep your responses concise and conversational. "
                "Follow the standard workflow of a licensed mental health expert, including assessment, diagnosis, therapeutic intervention, progress tracking, and crisis management. "
                "Maintain a warm, professional, and non-judgmental tone in all interactions.\n\n"
                "### Guidelines:\n"
                "- **Structured Responses:** Format responses in a clear and structured way using bullet points, numbered lists, and line breaks.\n"
                "- **Bold text** for emphasis.\n"
                "- Bullet points (`•`) for lists.\n"
                "- Numbered lists (`1., 2.`) where appropriate.\n"
                "- Line breaks (`\\n`) for readability.\n"
                "Make the response clear and structured."
                "- **Markdown Formatting:** Use Markdown to improve readability and ensure clarity in all responses.\n"
                "- **Human-Like Interaction:** Ensure responses feel natural, engaging, and supportive.\n"
                "- **Therapeutic Techniques:** Apply cognitive-behavioral therapy (CBT), mindfulness techniques, and evidence-based mental health practices.\n"
                "- **Assessment & Progress Tracking:** Gather information, provide insights, and track user well-being over time.\n"
                "- **Crisis Handling:** If the user indicates distress or harm, offer immediate support and suggest seeking professional help.\n"
                "- **Confidentiality & Ethics:** Prioritize privacy and provide non-judgmental, ethical support without giving medical prescriptions.\n\n"
                "Always respond with clarity, empathy, and professionalism, ensuring a supportive experience for the user."
    }
    conversation_history = [system_message] + user_chat_history[user_name]

    # Get AI-generated response
    bot_reply = analyze_responses_with_together(conversation_history)

    # Append bot response to user history
    user_chat_history[user_name].append({"role": "assistant", "content": bot_reply})

    return jsonify({'reply': bot_reply, 'history': user_chat_history[user_name], 'status': 'response'})

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

    # Initialize assessment state for the user
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

@app.route('/')
def index():
    return "Welcome to the Mental Health Chatbot Backend using Together API!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)