#!/usr/bin/env python3
"""
Run the Banking Chatbot API server.
"""
import uvicorn
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Run Banking Chatbot API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")

    args = parser.parse_args()

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set!")
        print("Please set it in .env file or export it:")
        print("  export ANTHROPIC_API_KEY=your-key-here")
        return 1

    print(f"Starting Banking Chatbot API...")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Reload: {args.reload}")
    print(f"  Workers: {args.workers}")
    print()
    print(f"API Docs: http://localhost:{args.port}/docs")
    print(f"Health Check: http://localhost:{args.port}/health")
    print()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info"
    )

    return 0


if __name__ == "__main__":
    exit(main())
