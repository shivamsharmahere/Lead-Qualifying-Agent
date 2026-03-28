import subprocess
import sys
import os
import time

def main():
    print("🚀 Starting AI-Powered Lead Capture Chatbot services...")
    
    # Start FastAPI server
    print("Starting FastAPI backend on port 8000...")
    fastapi_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Give the backend a second to initialize before starting the frontend
    time.sleep(2)
    
    # Start Streamlit dashboard
    print("Starting Streamlit dashboard on port 8501...")
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "dashboard/main.py", "--server.port", "8501"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    try:
        # Wait for both processes
        fastapi_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        fastapi_process.wait()
        streamlit_process.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
