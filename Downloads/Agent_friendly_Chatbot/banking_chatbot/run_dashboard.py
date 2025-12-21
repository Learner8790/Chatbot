#!/usr/bin/env python3
"""
Run the Streamlit Admin Dashboard.
"""
import subprocess
import sys
import os


def main():
    print("Starting Banking Chatbot Admin Dashboard...")
    print()
    print("Dashboard URL: http://localhost:8501")
    print()
    print("Make sure the API server is running on http://localhost:8000")
    print()

    # Get the dashboard path
    dashboard_path = os.path.join(
        os.path.dirname(__file__),
        "app", "dashboard", "admin.py"
    )

    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        dashboard_path,
        "--server.port=8501",
        "--server.address=localhost"
    ])


if __name__ == "__main__":
    main()
