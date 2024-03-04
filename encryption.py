from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from settings import KEY

def pad_key(key):
    while len(key) % 32 != 0:
        key += "P"
    return key
cipher = Fernet(urlsafe_b64encode(pad_key(KEY).encode()))
