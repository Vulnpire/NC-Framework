from http.server import *

PORT = 1337

BIND_ADDR = ""

class C2Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(404)
        self.end_headers()

server = HTTPServer((BIND_ADDR, PORT), C2Handler)

server.serve_forever()
