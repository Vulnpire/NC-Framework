## NecroNet Command Framework (NCF)

Command and Control Framework designed for red team operations. With its robust capabilities and technical prowess, NCF empowers you to orchestrate and manage complex operations with ease.

Features:

   * Advanced Command and Control: Take full control of remote systems with advanced command execution and control capabilities.
   * Secure Communication: Utilize encrypted communication channels to ensure the confidentiality and integrity of data transmission.
   * Multi-platform Support: Supports both Windows and Linux environments, offering flexibility in deployment and operation.
   * Stealth Operations: Conduct operations covertly with stealthy techniques to evade detection and maintain operational security.
   * File Transfer and Management: Seamlessly transfer files between systems and manage them efficiently with built-in file transfer functionalities.
   * Keylogging and Clipboard Monitoring: Monitor keystrokes and clipboard activities to gather critical information during operations.
   * Screen Capture and Control: Capture screenshots and control remote screens to gather visual intelligence and conduct operations effectively.
   * Audio Playback: Play audio files on remote systems for various purposes, including deception and distraction.
   * Conversion to Executables: Easily convert Python scripts to executable files using PyInstaller for simplified deployment.

Setup and Configuration:

   Clone the NCF repository to your local machine:
     `
     git clone https://github.com/Vulnpire/NC-Framework
     `
   Setting Up the C2 Server:

   * Navigate to the c2_server directory. `cd NC-Framework`
   * Modify the settings.py file to configure server settings such as port number, encryption keys, and log files. `ex <file>`
   * Run the `python3 nc_server.py`.

Initialization:

   * Initialize the NecroNet Command Framework by running the appropriate client script (windows_client.py for Windows or linux_client.py for Linux) on the target system.
   * Ensure that the Python environment is properly configured, and all dependencies are installed before executing the client script.

   * The `windows_client.py` script serves as a Windows client for a remote access framework, enabling remote control and management of Windows systems.
   * The `linux_client.py` script serves as a Linux client for a remote access framework, allowing remote control and management of Linux systems.
   * The `headless_lin_client.py` script serves as a headless Linux client for a remote access framework, allowing remote control and management of Linux systems.

linux_client.py:

   * The linux_client.py script is designed to run on Linux systems and provides a full-featured client interface for the NecroNet Command Framework (NCF).
   * It offers a comprehensive set of functionalities for executing commands, transferring files, capturing screens, logging keystrokes, and more.
   * You can interact with the linux_client.py script directly on a Linux-based operating system, either through a graphical user interface (GUI) or a terminal interface.

headless_lin_client.py:

   * The headless_lin_client.py script is a lightweight, headless version of the NCF client tailored for Linux systems.
   * Unlike the linux_client.py script, the headless_lin_client.py script operates without a graphical user interface (GUI) or user interaction.
   * It is designed for use in headless server environments or automated workflows where direct user interaction is not required.
   * The headless_lin_client.py script offers similar functionalities to the linux_client.py script but focuses on command-line execution and automation capabilities.

Choosing Between headless_lin_client.py and linux_client.py:

Use linux_client.py When:

 * You need a full-featured client interface with graphical or terminal interaction on a Linux system.
 * User interaction and direct control over client operations are desired.
 * You are running the client script in a desktop or workstation environment.

Use headless_lin_client.py When:

  * You require a lightweight, headless client for automated tasks or server environments.
  * Graphical user interface (GUI) interaction is not necessary, and you prefer command-line operation.
  * You are deploying the client script in a headless server environment or for batch processing tasks.

Conversion to Executable (Optional):

To distribute the client script as a standalone executable file, follow these steps:

  Install PyInstaller using pip: `pip3 install pyinstaller`
    
  Run PyInstaller to convert the .py file to .exe: `pyinstaller --onefile windows_client.py`

Server Help:

  `server help`: Retrieve information about available server commands and usage.

Client Commands:

  Command Execution:
  
 * Execute system commands directly on the client using the format: `COMMAND <params>`.

File Operations:

  * Download Files: `client download FILENAME`: Download files from the server to the client.
  * Upload Files: `client upload FILENAME`: Upload files from the client to the server.
  * Zip Files: `client zip FILENAME`: Zip-encrypt files on the client.
  * Unzip Files: `client unzip FILENAME`: Unzip and decrypt files on the client.

Other Actions:

  * Kill Client: `client kill`: Shutdown the client.
  * Set Delay: `client delay SECONDS`: Adjust the delay between re-connection attempts.
  * Clipboard Interaction: `client get clipboard`: Retrieve clipboard contents from the client.
  * Key Logging: `client keylog on/off`: Start or stop key logging on the client.
  * Type Text: `client type TEXT`: Simulate typing text on the client's keyboard.
  * Capture Screenshots: `client screenshot`: Capture and save screenshots on the client.
  * Display Images: `client display IMAGE`: Display images on the client's screen.
  * Manipulate Screen Orientation: `client flip/roll screen`: Flip or roll the client's screen orientation.
  * Adjust Volume: `client max volume`: Maximize the client's volume.
  * Play Audio Files: `client play FILENAME.wav`: Play audio files on the client.

Disclaimer:

NecroNet Command Framework is intended for educational and cybersecurity research purposes only. Unauthorized use of this framework for malicious activities is strictly prohibited. I am not liable for any misuse or damage caused by its use.
