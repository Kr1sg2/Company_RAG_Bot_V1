#!/bin/bash

echo "🚀 Starting LexaAI..."

# Navigate to the LexaAI folder
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI || exit

# Activate the virtual environment
echo "📢 Activating Virtual Environment..."
source venv/bin/activate

# Start FastAPI Backend
echo "⚡ Starting FastAPI server on port 8600..."
uvicorn app:app --host 0.0.0.0 --port 8600 --reload &

# Wait for 5 seconds to allow FastAPI to start
sleep 5

# Start Streamlit Frontend
echo "🖥️ Starting Streamlit app on port 8501..."
streamlit run streamlit_app.py

echo "✅ LexaAI is now running! Access it at http://localhost:8501"
