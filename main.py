import os
import random
import socket
import threading
import wave
from hashlib import sha256
from math import ceil

from loguru import logger

import wx
import wx.lib.agw.genericmessagedialog as GMD
from Crypto.Cipher import AES

import send_receive_encrypted
import sound_manager
from tcp_by_size import send_with_size, recv_by_size
import pyaudio

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 2525  # Port to listen on (non-privileged ports are > 1023)
server_socket = ''

# Encryption variables
is_encrypted = False
iv_parms = ''
aes_key = ''
Username = "mr know all"

target_sound_file = "sound_recording.wav"
recording_file = "recording.wav"

rec = True


def stop_record():
    global rec
    rec = False


class LoginDialog(wx.Dialog):
    def __init__(self):
        super().__init__(None, title="Login")

        # Create sizers for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer = wx.BoxSizer(wx.VERTICAL)

        # Username label and text box
        email_label = wx.StaticText(self, label="Username:")
        self.username_text = wx.TextCtrl(self)  # Store as instance variable
        input_sizer.Add(email_label, 0, wx.ALL, 5)
        input_sizer.Add(self.username_text, 0, wx.EXPAND | wx.ALL, 5)

        # Password label and text box
        password_label = wx.StaticText(self, label="Password:")
        self.password_text = wx.TextCtrl(self, style=wx.TE_PASSWORD)  # Store as instance variable
        input_sizer.Add(password_label, 0, wx.ALL, 5)
        input_sizer.Add(self.password_text, 0, wx.EXPAND | wx.ALL, 5)

        # Button sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        login_button = wx.Button(self, label="Login")
        signup_button = wx.Button(self, label="Sign Up")
        button_sizer.Add(login_button, 1)
        button_sizer.Add(signup_button, 1)

        # Add sizers to main sizer
        main_sizer.Add(input_sizer, 1, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)

        # Set main sizer and show dialog
        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_login, login_button)  # Bind login button press event
        self.Bind(wx.EVT_BUTTON, self.on_signup, signup_button)  # Bind signup button press event

        self.ShowModal()

    def on_login(self, event):
        global Username
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()
        message = "Login~" + username + "~" + password
        to_send = convert_with_length_prefix(message)
        send_receive_encrypted.send_encrypted(server_socket, to_send, aes_key, iv_parms)
        data = recv_by_size(server_socket).decode("utf-8")
        if data == "Username and password match":
            Username = username
            GMD.GenericMessageDialog(None, "Username and password match", "Login Information",
                                     wx.OK | wx.ICON_INFORMATION)
            self.Hide()
            post_login_dialog = RecordSound(self)
            post_login_dialog.ShowModal()
            post_login_dialog.Destroy()
            self.Show()
        else:
            wx.MessageBox("Invalid username and password", "Login Information", wx.OK | wx.ICON_INFORMATION)

    def on_signup(self, event):
        self.Hide()
        signup_dialog = SignupDialog(self)
        signup_dialog.ShowModal()
        signup_dialog.Destroy()
        self.Show()


def send_sound_(code, current, file_length, content):
    msg = code + "~" + Username + "~" + str((1 if current == file_length else 0)) + "~"
    to_send = convert_with_length_prefix(msg)
    message_plus_content = bytearray()
    message_plus_content.extend(to_send)
    message_plus_content.extend(content)
    send_with_size(server_socket, message_plus_content)
    recv_by_size(server_socket).decode("utf-8")


def send_sound(file_path, code):
    current = 0
    file_length = os.stat(file_path).st_size
    with open(file_path, "rb") as f:
        while current < file_length:
            size = 40000
            if file_length - current >= size:
                current += size
            else:
                size = file_length - current
                current = file_length
            send_sound_(code, current, file_length, f.read(size))


def save_sound(file_path, sound_name):
    send_sound(file_path, "SaveRecord" + "~" + sound_name)


# def send_recording_(code, content):
#     msg = code + "~" + Username + "~"
#     to_send = convert_with_length_prefix(msg)
#     message_plus_content = bytearray()
#     message_plus_content.extend(to_send)
#     message_plus_content.extend(content)
#     send_with_size(server_socket, message_plus_content)
#     return recv_by_size(server_socket).decode("utf-8")


def send_recording(file_path, code):
    while(rec):
        sound_manager.record_to_file(file_path)
        send_sound(file_path, code)


def send_selection(sound_name):
    logger.info("User's selection {}", sound_name)
    msg = "ShortRecordExist" + "~" + Username + "~" + sound_name + "~"
    to_send = convert_with_length_prefix(msg)
    # message_plus_content = bytearray()
    # message_plus_content.extend(to_send)
    send_with_size(server_socket, to_send)
    recv_by_size(server_socket).decode("utf-8")


class RecordSound(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Sound Recording")

        # Create sizers for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Record and Next buttons
        record_button = wx.Button(self, label="Record")
        next_button = wx.Button(self, label="Next")
        save_button = wx.Button(self, label="Save")
        play_button = wx.Button(self, label="Play")

        main_sizer.Add(record_button, 0, wx.ALL | wx.CENTER, 10)
        main_sizer.Add(next_button, 0, wx.ALL | wx.CENTER, 10)
        main_sizer.Add(save_button, 0, wx.ALL | wx.CENTER, 10)
        main_sizer.Add(play_button, 0, wx.ALL | wx.CENTER, 10)

        # Create a spinner (choice control) with a default value
        self.spinner = wx.Choice(self, choices=["default"])
        main_sizer.Add(self.spinner, 0, wx.ALL | wx.CENTER, 10)

        # Set main sizer and show dialog
        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_record, record_button)  # Bind record button press event
        self.Bind(wx.EVT_BUTTON, self.on_next, next_button)  # Bind next button press event
        self.Bind(wx.EVT_BUTTON, self.on_save, save_button)  # Bind save button press event
        self.Bind(wx.EVT_BUTTON, self.on_play, play_button)  # Bind play button press event

        # Call method to initialize spinner values when the dialog is created
        self.initialize_spinner()

    def initialize_spinner(self):
        values = self.get_sounds()
        # Add values to the spinner, keeping "default" as the first item
        self.spinner.SetItems(["default"] + values)
        self.spinner.SetSelection(0)  # Set default selection to "default"

    def get_sounds(self):
        msg = "GetSoundsNames" + "~" + Username + "~"
        to_send = convert_with_length_prefix(msg)
        # message_plus_content = bytearray()
        # message_plus_content.extend(to_send)
        send_with_size(server_socket, to_send)
        value_in_string = recv_by_size(server_socket).decode("utf-8")

        # Split the string by "~" and filter out empty strings
        sounds = value_in_string.split("~")
        saved_recording_names = [sound for sound in sounds if sound]

        return saved_recording_names

    def on_save(self, event):
        # Handle save button press
        text_dialog = wx.TextEntryDialog(self, "Enter text:", "Save Recording")
        if text_dialog.ShowModal() == wx.ID_OK:
            entered_text = text_dialog.GetValue()
            if entered_text not in self.spinner.GetItems():
                save_sound(target_sound_file, entered_text)
                self.spinner.Append(entered_text)
            else:
                wx.MessageBox(f"Entry already exists in spinner: {entered_text}", "Info", wx.OK | wx.ICON_INFORMATION)
        text_dialog.Destroy()

    def on_play(self, event):
        # Handle play button press
        # define stream chunk
        chunk = 1024

        # open a wav format music
        f = wave.open(target_sound_file, "rb")
        # instantiate PyAudio
        p = pyaudio.PyAudio()
        # open stream
        stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        # read data
        data = f.readframes(chunk)

        # play stream
        while data:
            stream.write(data)
            data = f.readframes(chunk)

            # stop stream
        stream.stop_stream()
        stream.close()

        # close PyAudio
        p.terminate()

    def on_record(self, event):
        sound_manager.record_sound(target_sound_file)
        wx.MessageBox("Sound captured", "Info", wx.OK | wx.ICON_INFORMATION)

    def on_next(self, event):
        # wx.MessageBox("Next button pressed", "Info", wx.OK | wx.ICON_INFORMATION)
        if self.spinner.GetStringSelection() == "default":
            send_sound(target_sound_file, "ShortRecordSave")
        else:
            send_selection(self.spinner.GetStringSelection())
        self.Hide()
        counter = Counter(self)
        counter.ShowModal()
        counter.Destroy()
        self.Show()


class Counter(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="occurrence counter")

        self.recording = False
        self.recording_thread = None

        # Create sizers for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Record and Next buttons
        self.record_button = wx.Button(self, label="Record")
        self.stop_button = wx.Button(self, label="Stop")
        self.stop_button.Disable()  # Initially disable stop button

        main_sizer.Add(self.record_button, 0, wx.ALL | wx.CENTER, 10)
        main_sizer.Add(self.stop_button, 0, wx.ALL | wx.CENTER, 10)

        # Set main sizer and show dialog
        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_record, self.record_button)  # Bind record button press event
        self.Bind(wx.EVT_BUTTON, self.on_stop, self.stop_button)  # Bind stop button press event

    def on_record(self, event):
        if not self.recording:
            self.recording = True
            self.stop_button.Enable()
            self.record_button.Disable()
            self.recording_thread = threading.Thread(target=send_recording, args=(recording_file, "LongRecordPy"))
            self.recording_thread.start()

    def on_stop(self, event):
        if self.recording:
            sound_manager.stop_record()
            stop_record()
            # self.recording_thread.join()  # Wait for recording thread to finish
            print("Stopped recording")
            self.recording = False
            self.record_button.Enable()
            self.stop_button.Disable()
            wx.MessageBox("Stopped recording", "Info", wx.OK | wx.ICON_INFORMATION)


class SignupDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Sign Up")

        # Create sizers for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer = wx.BoxSizer(wx.VERTICAL)

        # Username label and text box
        email_label = wx.StaticText(self, label="Username:")
        self.username_text = wx.TextCtrl(self)  # Store as instance variable
        input_sizer.Add(email_label, 0, wx.ALL, 5)
        input_sizer.Add(self.username_text, 0, wx.EXPAND | wx.ALL, 5)

        # Password label and text box
        password_label = wx.StaticText(self, label="Password:")
        self.password_text = wx.TextCtrl(self, style=wx.TE_PASSWORD)  # Store as instance variable
        input_sizer.Add(password_label, 0, wx.ALL, 5)
        input_sizer.Add(self.password_text, 0, wx.EXPAND | wx.ALL, 5)

        # Signup button
        signup_button = wx.Button(self, label="Sign Up")
        main_sizer.Add(input_sizer, 1, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(signup_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # Set main sizer and show dialog
        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_signup, signup_button)  # Bind signup button press event

    def on_signup(self, event):
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()
        message = "SignUp~" + username + "~" + password
        to_send = convert_with_length_prefix(message)
        send_receive_encrypted.send_encrypted(server_socket, to_send, aes_key, iv_parms)
        data = recv_by_size(server_socket).decode("utf-8")
        if data == "Sign up successful":
            wx.MessageBox("Registered successfully", "Login Information", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Username is in use", "Login Information", wx.OK | wx.ICON_INFORMATION)
        self.EndModal(wx.ID_OK)


def set_encryption(sock):
    global is_encrypted
    global iv_parms
    global aes_key
    if not is_encrypted:
        data = b'Please talk with my secretly'
        send_with_size(sock, data)
        DPH_srv_key = recv_by_size(sock).decode()

        parts = DPH_srv_key.split("|")
        srv_public_key = int(parts[0])
        g = int(parts[1])
        p = int(parts[2])

        client_private_key = random.getrandbits(2048)
        client_public_key = pow(g, client_private_key, p)

        send_with_size(sock, client_public_key.to_bytes(ceil(client_public_key.bit_length() / 8.0)))
        # key_size = (16, 24, 32)
        SharedKey = pow(srv_public_key, client_private_key, p)
        secret_key = sha256(str(SharedKey).encode()).digest()[:16]

        aes_key = secret_key
        cipherEncryption = AES.new(secret_key, AES.MODE_CBC)
        send_with_size(sock, cipherEncryption.IV)

        iv_parms = cipherEncryption.IV  # AES.new(secret_key, AES.MODE_CBC, aes_key.IV).IV

        is_encrypted = True


def convert_with_length_prefix(text):
    """Converts text to bytes and prepends the length as a single byte.

    Args:
      text: The text string to be converted.

    Returns:
      A byte array with the length prefix followed by the encoded text.
    """
    # Convert text to bytes with UTF-8 encoding (adjust encoding if needed)
    message_bytes = text.encode("utf-8")

    # Get the message length (number of bytes)
    message_length = len(message_bytes)

    # Combine length byte (single byte) and message bytes
    prefixed_bytes = bytearray((message_length,)) + message_bytes
    return prefixed_bytes


def main():
    # sound_manager.record_to_file_with_key(recording_file, 'q')
    global server_socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            s.connect((HOST, PORT))
            set_encryption(s)
            server_socket = s

            app = wx.App()
            LoginDialog()
            app.MainLoop()
    except (ConnectionRefusedError, OSError) as e:
        print("Connection refused")

        # text = "Hello World!"
        #
        # send_receive_encrypted.send_encrypted(s, convert_with_length_prefix(text), aes_key, iv_parms)
        # data = s.recv(1024)


if __name__ == '__main__':
    main()
