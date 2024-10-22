#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Run the FastAPI app in the background, outputting to a log file
nohup uvicorn main:app --port 8000 --host 0.0.0.0 > fastapi.log 2>&1 &

# Display a message
echo "Process on port 8000 started."