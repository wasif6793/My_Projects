import streamlit as st
import requests
import mysql.connector
import pymongo
from pymongo import MongoClient
import random
import webbrowser
from datetime import datetime

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017")
db = client["chatbot_db"]
chat_history = db["chat_history"]
quizzes = db["quizzes"]
quiz_history = db["quiz_history"]

# MySQL Setup
def get_user_from_mysql(username):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",  # Change this to your MySQL password
            database="chatbot_auth"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

# Function to chat with Ollama API
def chat_with_ollama(prompt, model="deepseek-r1:latest", is_chat=False):
    url = "http://localhost:11434/api/generate"
    
    if is_chat:
        # Enhanced prompt for chat to get detailed answers
        enhanced_prompt = f"""You are a helpful teaching assistant. Please provide a detailed answer to the following question.
        Requirements:
        1. Answer length should be between 50-100 words
        2. Include relevant examples or analogies
        3. Break down complex concepts into simpler terms
        4. Use clear and concise language
        5. If applicable, mention real-world applications
        
        Question: {prompt}
        
        Please provide your answer:"""
        data = {
            "model": model,
            "prompt": enhanced_prompt,
            "stream": False
        }
    else:
        # Original prompt for quiz generation
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.ConnectionError:
        return "I apologize, but I'm currently unable to connect to the AI model."
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}."

# Function to get YouTube link based on the topic
def get_youtube_link(topic):
    search_query = f"{topic} educational video"
    youtube_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
    return youtube_url

# Function to generate quiz questions using Ollama
def generate_quiz_questions(topic, difficulty="easy"):
    prompt = f"""Generate 5 {difficulty} multiple choice questions about {topic}. Each question should:
    1. Not exceed 20 words
    2. Have 4 options (A, B, C, D)
    3. Include the correct answer
    4. For {difficulty} level:
       - Easy: Basic facts and simple concepts
       - Medium: More detailed understanding required
       - Hard: Complex concepts and deeper knowledge needed
    Format the response as JSON with this structure:
    {{
        "questions": [
            {{
                "question": "question text",
                "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
                "correct_answer": "A/B/C/D"
            }}
        ]
    }}
    Make the questions educational and appropriate for {difficulty} level."""
    
    try:
        response = chat_with_ollama(prompt)
        # Extract JSON from the response
        import json
        import re
        json_str = re.search(r'\{.*\}', response, re.DOTALL)
        if json_str:
            return json.loads(json_str.group())
        else:
            st.error("Failed to generate proper quiz format")
            return None
    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        return None

# Function to clear session and logout
def logout():
    # Clear all session state variables
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Redirect to login page
    webbrowser.open("http://localhost:8080/login")

# Streamlit Page Setup
def main():
    st.set_page_config(page_title="AI Learning Assistant", page_icon="🎓")
    
    # Initialize session state
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    
    # Get username from URL parameters
    if 'username' in st.query_params:
        st.session_state.username = st.query_params['username']
    
    if st.session_state.username:
        user = get_user_from_mysql(st.session_state.username)
        if user:
            st.title(f"Welcome {user['fullname']} to your Learning Dashboard")
            
            # Sidebar for navigation and logout
            with st.sidebar:
                st.title("Navigation")
                page = st.radio("Go to", ["Chat", "Quiz", "Quiz History", "Chat History"])
                
                # Add a separator
                st.markdown("---")
                
                # Add logout button at the bottom of sidebar
                st.markdown("### Account")
                if st.button("Logout", type="primary"):
                    logout()
            
            if page == "Chat":
                st.subheader("Chat with AI Assistant")
                st.write("Ask any question and get a detailed explanation (50-100 words)")
                user_input = st.text_input("Ask your question:")
                
                if user_input:
                    with st.spinner("Thinking..."):
                        response = chat_with_ollama(
                            user_input,
                            is_chat=True  # This will trigger the enhanced prompt
                        )
                        st.write(f"Assistant: {response}")
                        
                        # Save chat history
                        chat_data = {
                            "username": st.session_state.username,
                            "user_input": user_input,
                            "response": response,
                            "timestamp": datetime.now()
                        }
                        chat_history.insert_one(chat_data)
                        
                        # Provide YouTube link
                        youtube_link = get_youtube_link(user_input)
                        st.write(f"Learn more: [Watch on YouTube]({youtube_link})")
            
            elif page == "Quiz":
                st.subheader("Quiz Time!")
                
                # Topic and difficulty selection
                col1, col2 = st.columns(2)
                with col1:
                    topic = st.text_input("Enter a topic for your quiz:")
                with col2:
                    difficulty = st.selectbox(
                        "Select difficulty level",
                        ["easy", "medium", "hard"],
                        format_func=lambda x: x.capitalize()
                    )
                
                if topic and st.button("Generate Quiz"):
                    with st.spinner(f"Generating {difficulty} quiz questions..."):
                        quiz_data = generate_quiz_questions(topic, difficulty)
                        if quiz_data:
                            st.session_state.current_quiz = quiz_data
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_submitted = False
                
                # Display quiz if available
                if st.session_state.current_quiz and not st.session_state.quiz_submitted:
                    st.write(f"### Your {difficulty.capitalize()} Quiz on {topic}")
                    for i, q in enumerate(st.session_state.current_quiz['questions']):
                        st.write(f"{i+1}. {q['question']}")
                        answer = st.radio(
                            f"Select your answer for question {i+1}",
                            options=q['options'],
                            key=f"q{i}"
                        )
                        st.session_state.quiz_answers[str(i)] = answer  # Convert index to string
                    
                    if st.button("Submit Quiz"):
                        # Calculate score
                        score = 0
                        for i, q in enumerate(st.session_state.current_quiz['questions']):
                            if st.session_state.quiz_answers[str(i)] == q['options'][ord(q['correct_answer']) - ord('A')]:
                                score += 1
                        
                        # Save quiz results
                        quiz_result = {
                            "username": st.session_state.username,
                            "topic": topic,
                            "difficulty": difficulty,
                            "score": score,
                            "total_questions": 5,
                            "questions": st.session_state.current_quiz['questions'],
                            "user_answers": st.session_state.quiz_answers,  # Now using string keys
                            "timestamp": datetime.now()
                        }
                        quiz_history.insert_one(quiz_result)
                        
                        st.session_state.quiz_submitted = True
                        st.success(f"Quiz submitted! Your score: {score}/5")
                
                elif st.session_state.quiz_submitted:
                    st.write("### Quiz Results")
                    for i, q in enumerate(st.session_state.current_quiz['questions']):
                        user_answer = st.session_state.quiz_answers[str(i)]  # Use string key
                        correct_answer = q['options'][ord(q['correct_answer']) - ord('A')]
                        st.write(f"Question {i+1}: {q['question']}")
                        st.write(f"Your answer: {user_answer}")
                        st.write(f"Correct answer: {correct_answer}")
                        st.write("---")
                    
                    if st.button("Take Another Quiz"):
                        st.session_state.current_quiz = None
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.experimental_rerun()
            
            elif page == "Quiz History":
                st.subheader("Your Quiz History")
                
                # Fetch all quizzes for the user
                user_quizzes = list(quiz_history.find(
                    {"username": st.session_state.username}
                ).sort("timestamp", -1))
                
                if user_quizzes:
                    for quiz in user_quizzes:
                        with st.expander(f"{quiz['difficulty'].capitalize()} Quiz on {quiz['topic']} - {quiz['timestamp'].strftime('%Y-%m-%d %H:%M')} - Score: {quiz['score']}/5"):
                            st.write(f"Topic: {quiz['topic']}")
                            st.write(f"Difficulty: {quiz['difficulty'].capitalize()}")
                            st.write(f"Score: {quiz['score']}/5")
                            st.write("Questions and Answers:")
                            for i, q in enumerate(quiz['questions']):
                                st.write(f"{i+1}. {q['question']}")
                                st.write(f"Your answer: {quiz['user_answers'][str(i)]}")  # Use string key
                                st.write(f"Correct answer: {q['options'][ord(q['correct_answer']) - ord('A')]}")
                                st.write("---")
                else:
                    st.write("No quiz history found. Take a quiz to see your results here!")
            
            elif page == "Chat History":
                st.subheader("Your Chat History")
                
                # Show chat history
                user_chats = list(chat_history.find(
                    {"username": st.session_state.username}
                ).sort("timestamp", -1).limit(10))
                
                for chat in user_chats:
                    with st.expander(f"Chat from {chat['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                        st.write(f"**You:** {chat['user_input']}")
                        st.write(f"**Assistant:** {chat['response']}")
        
        else:
            st.error("User not found! Please register first.")
            st.button("Go to Registration", on_click=lambda: webbrowser.open("http://localhost:8080/register"))
    else:
        st.error("Please log in first!")
        st.button("Go to Login", on_click=lambda: webbrowser.open("http://localhost:8080/login"))

if __name__ == "__main__":
    main()
