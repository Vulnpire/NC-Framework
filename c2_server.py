from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 1337

BIND_ADDR = ""

class C2Handler(BaseHTTPRequestHandler):
    """ This is a child class of the BaseHTTPRequestHandler class.  It handles all HTTP requests that arrive at the c2
    server."""

    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"

    def do_GET(self):
        """ This method handles all HTTP GET requests that arrive at the c2 server. """

        self.send_response(404)
        self.end_headers()


print("server_version: ", C2Handler.server_version)
print("sys_version: ", C2Handler.sys_version)

server = HTTPServer((BIND_ADDR, PORT), C2Handler)

server.serve_forever()
