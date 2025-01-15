# Find the PID of the process using port 8000
PID=$(lsof -t -i :8000)

# Check if a process was found and kill it
if [ -z "$PID" ]; then
    echo "No process is running on port 8000."
else
    echo "Killing process on port 8000 with PID: $PID"
    kill -9 $PID
    echo "Process on port 8000 stopped."
fi