from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 1337

BIND_ADDR = ""

CMD_REQUEST = "/book?isbn="

class C2Handler(BaseHTTPRequestHandler):

    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"

    def do_GET(self):

        if self.path.startswith(CMD_REQUEST):
            client = self.path.split(CMD_REQUEST)[1]
            print(client)

        self.send_response(404)
        self.end_headers()


server = HTTPServer((BIND_ADDR, PORT), C2Handler)

server.serve_forever()
