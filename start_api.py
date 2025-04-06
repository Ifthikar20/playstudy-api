"""
Simple development server for the PlayStudy API without DB features.
This version bypasses DynamoDB completely and uses in-memory mock data.
"""

import os
import uvicorn

# Set environment variables for development
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "thisisasecretkey1234567890thisisasecretkey"
os.environ["MOCK_DB"] = "True"

if __name__ == "__main__":
    print("Starting PlayStudy API in mock mode (no DynamoDB)")
    print("This is for development and testing only!")
    print("API documentation: http://localhost:8080/docs")
    
    # Start the API
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )