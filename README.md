# Harmonic - PC Client (Python)

This repository contains the Python-based client-side code for Harmonic, an application designed to automate the counting of short sound segments within longer recordings. Harmonic simplifies the process of repetitive sound counting, freeing users from manual effort and allowing them to focus on more important tasks. A complete description of the project architecture and overall functionality, including the server-side components, can be found in the [server-side](https://github.com/TheBunder/HarmonicServer) repository.

Harmonic addresses the common need to count recurring sounds within a longer audio clip. For example, a user can record the sound of a single keyboard key press and then record a longer session of typing. Harmonic will then automatically count how many times that key press sound occurred in the recording. This automation has broad applications, from enhancing sports performance (e.g., counting punches or jump rope repetitions) to research and data analysis.

## System Description

Harmonic consists of the following key components:

* **User Authentication:** The PC client includes a secure login system, enabling users to access their personal account. This ensures that user data and recordings are protected.
* **Sound Recording:** Users can record short sound segments, which will be used in later analysis. Additionally, users have the option to save these sound segments within the app for future reference and analysis. This allows users to build a library of sounds for different counting tasks.
* **Sound Comparison and Counting:** Recorded sound segments are sent to the server for similarity comparison and occurrence counting. The server uses FFT for this analysis.
* **Data Encryption:** Users' personal information is encrypted before transmission to the server to ensure secure data handling using AES and Diffie–Hellman encryptions.
* **Server Interaction:** The application communicates with a server, transmitting sound data for analysis and receiving occurrence counts. This client-server architecture allows for efficient processing of audio data.

## Features

* **Sound Segment Recording:** Users can easily record short sound segments (e.g., a single key press, a specific sound event) using the PC's microphone.
* **Long Recording Analysis:** Users can record longer audio clips (e.g., a typing session, a workout) using the PC's microphone to be analyzed for the frequency of the short sound segment.
* **Automated Counting:** Harmonic automatically counts the occurrences of the short sound within the long recording, eliminating manual counting.
* **Real-time Results:**  The PC client displays results in real-time.

## Technologies Used

* Python 
* wxPython (for GUI)
* PyAudio (for audio recording)
* `socket` (for network communication)
* `threading` (for concurrent recording and UI responsiveness)
* `wave` (for audio file handling)
* `hashlib` (for SHA256 hashing)
* PyCryptodome (for AES encryption - You mentioned `Crypto.Cipher.AES`, which is part of PyCryptodome)
* `loguru` (for logging)
* `re` (for regular expressions)
* `base64` (for encoding/decoding data)
* `time` (for managing recording durations)
* `struct` (for packing data)
* `sys` (for system information)
* `array` (for array manipulation)
## Installation

1. **Prerequisites:**
    * Python installed on your system.
    * Poetry installed on your system.  You can install Poetry using:
       ```bash
       pip install poetry
       ```
    * **Important:** The client application and the server *must* be on the same private network (e.g., behind a NAT router). This is essential for communication between the client and server.

2. **Steps:**

    1. Clone the repository:
       ```bash
       git clone (https://github.com/TheBunder/client_harmonic.git)
       ```

    2. Navigate to the project directory:

    3. Install the project dependencies using Poetry:
       ```bash
       poetry install
       ```
       *(Poetry will automatically create a virtual environment and install the dependencies listed in your `pyproject.toml` file.)*

## Usage

1.  Run the Harmonic PC client: `python main.py`
### Sign-Up Screen
1.  Enter your desired username in the username field.
2.  Enter a password that is at least 6 characters long in the password field.
3.  Click the "Register" button.
4.  A message will appear indicating whether the registration was successful. If the username is already in use, you will be prompted to choose a different username.

### Log-In Screen

1.  Enter your registered username in the username field.
2.  Enter your password in the password field.
3.  Click the "Login" button.
4.  If the username and password are correct, you will be taken to the Short Sound Recording screen. Otherwise, you will be prompted to re-enter your credentials or sign up for a new account.

### Short Sound Recording Screen

1.  Click the "Record" button to begin recording the short sound segment.
2.  The recording will stop automatically.
3.  Click the "Play" button to listen to your recording.
4.  To save the recording:
    1.  Click the "Save" button.
    2.  A pop-up dialog will appear, prompting you to enter a name for the recording.
    3.  Enter a unique name and click "Save" in the dialog. If the name is already in use, you will be asked to enter a different name.
5.  To load a previously saved recording, click the dropdown menu (spinner) and select the desired recording.
6.  To return to the currently recorded sound after selecting a saved sound, choose "default" in the spinner.
7.  Click the "Next" button to proceed to the Long Recording screen.

### Long Recording Screen

1.  Click the "Record" button to begin recording the long audio clip.
2.  Click the "Stop" button to stop recording.
3.  The app will display the count of occurrences of the short sound segment in real-time at the bottom of the screen.

## Relationship to Server

The PC client-side application interacts with the server-side API by sending the raw audio data to the server for analysis. The server returns the count of the short sound segments, which the client then displays to the user. The server-side code is responsible for processing audio data using the FFT algorithm, providing user authentication using username and password.

## Screenshots

![PC_screens](https://github.com/user-attachments/assets/2acd068b-5303-4170-b8e7-bcd2578cc3ff)
