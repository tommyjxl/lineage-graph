#!/bin/bash
#
# This script starts a local web server and opens the data lineage graph visualization.
#

# The port for the HTTP server
PORT=8000
# The file to open in the browser
FILE_TO_OPEN="src/force-graph.html"
# The directory where the web content is located
WEB_DIR="."
# The URL to open
URL="http://localhost:${PORT}/${FILE_TO_OPEN}"
# The process name for the python http server
PROCESS_NAME="python -m http.server"
# The PID of the existing server process
PID=$(pgrep -f "${PROCESS_NAME}")

# Check for and kill any existing server process
if [ -n "$PID" ]; then
  echo "Found a running web server on PID ${PID}. Stopping it now..."
  kill "${PID}"
  # Wait a moment for the port to be released
  sleep 1
fi

echo "Starting a new web server in the background..."
# Start the server in the background from the project root
(python -m http.server "${PORT}" &)
# Wait a moment for the server to start
sleep 2

echo "Opening ${URL} in your browser..."

# Open the URL in the default browser (works on macOS and most Linux distributions)
# Use 'start' on Windows
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "cygwin"* ]]; then
  xdg-open "${URL}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  open "${URL}"
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "win32"* ]]; then
  start "${URL}"
else
  echo "Unsupported OS. Please open the URL manually in your browser: ${URL}"
fi