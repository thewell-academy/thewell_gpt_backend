#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Run the FastAPI app in the background, outputting to a log file
uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=key.pem --ssl-certfile=cert.pem > fastapi.log 2>&1 & > fastapi.log 2>&1 &

# Display a message
echo "Process on port 8000 started."