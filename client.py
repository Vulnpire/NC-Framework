#!/bin/python3

from requests import *

HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"}


x = get('http://localhost:1337', headers=HEADER)
print(x.request.headers)
