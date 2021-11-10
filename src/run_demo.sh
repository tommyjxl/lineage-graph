osascript -e 'tell application "Terminal" to activate' \
  -e 'tell application "System Events" to tell process "Terminal" to keystroke "t" using command down' \
  -e 'tell application "Terminal" to do script "python -m http.server" in selected tab of the front window'

sleep 1

open -a /Applications/Google\ Chrome.app/ http://localhost:8000/force-graph.html
