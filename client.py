from requests import get

HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"}

# Set a proxy
# PROXY = {"https": "proxy:8081"}
PROXY = None
PORT = 80
C2_SERVER = "localhost"

x = get(f"http://{C2_SERVER}:{PORT}", headers=HEADER, proxies=PROXY)
print(x.headers)
