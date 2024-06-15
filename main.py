import os
import socket
import threading
import wave

from loguru import logger

import wx
import wx.lib.agw.genericmessagedialog as GMD

import send_receive_encrypted
import sound_manager
from tcp_by_size import send_with_size, recv_by_size
import pyaudio

import re

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 2525  # Port to listen on (non-privileged ports are > 1023)
server_socket = ''

Username = "mr know all"

target_sound_file = "sound_recording.wav"
recording_file = "recording.wav"

rec = True

occurrences = 0

MINIMUM_PASSWORD_LENGTH = 6


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
        username_label = wx.StaticText(self, label="Username:")
        self.username_text = wx.TextCtrl(self)  # Store as instance variable
        input_sizer.Add(username_label, 0, wx.ALL, 5)
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
        if not (password == "" or username == ""):
            message = "Login~" + username + "~" + password
            to_send = convert_with_length_prefix(message)
            send_receive_encrypted.send_encrypted(server_socket, to_send)
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
        else:
            wx.MessageBox("Please enter all the fields as mentioned", "Login Information", wx.OK | wx.ICON_INFORMATION)

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
    return recv_by_size(server_socket).decode("utf-8")


def send_sound(file_path, code):
    current = 0
    file_length = os.stat(file_path).st_size
    global occurrences
    with open(file_path, "rb") as f:
        while current < file_length:
            size = 40000
            if file_length - current >= size:
                current += size
            else:
                size = file_length - current
                current = file_length
            message = send_sound_(code, current, file_length, f.read(size))
            if "Number" in message:
                occurrences += int(message.split(" ")[3])


def save_sound(file_path, sound_name):
    send_sound(file_path, "SaveRecord" + "~" + sound_name)


def send_recording(file_path, code, text: wx.StaticText):
    while (rec):
        sound_manager.record_to_file(file_path)
        send_sound(file_path, code)
        text.SetLabel("Number of occurrences: " + str(occurrences))


def send_selection(sound_name):
    logger.info("User's selection {}", sound_name)
    msg = "ShortRecordExist" + "~" + Username + "~" + sound_name + "~"
    to_send = convert_with_length_prefix(msg)
    send_with_size(server_socket, to_send)
    recv_by_size(server_socket).decode("utf-8")


class RecordSound(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Sound Recording", size=(400, 350))

        # Create sizers for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Record and Next buttons
        record_button = wx.Button(self, label="Record")
        next_button = wx.Button(self, label="Next")
        play_button = wx.Button(self, label="Play")
        optional_text = wx.StaticText(self, label="optional:")
        save_button = wx.Button(self, label="Save")

        main_sizer.Add(record_button, 0, wx.ALL | wx.CENTER, 10)
        main_sizer.Add(next_button, 0, wx.ALL | wx.CENTER, 10)
        main_sizer.Add(play_button, 0, wx.ALL | wx.CENTER, 10)
        main_sizer.Add(optional_text, 0, wx.ALL | wx.CENTER, 10)
        main_sizer.Add(save_button, 0, wx.ALL | wx.CENTER, 10)

        # Create a spinner (choice control) with a default value
        self.spinner = wx.Choice(self, choices=["default"])
        main_sizer.Add(self.spinner, 0, wx.ALL | wx.CENTER, 10)

        # Set main sizer and show dialog
        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_record, record_button)  # Bind record button press event
        self.Bind(wx.EVT_BUTTON, self.on_next, next_button)  # Bind next button press event
        self.Bind(wx.EVT_BUTTON, self.on_play, play_button)  # Bind play button press event
        self.Bind(wx.EVT_BUTTON, self.on_save, save_button)  # Bind save button press event

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
        super().__init__(parent, title="occurrence counter", size=(400, 200))

        self.recording = False
        self.recording_thread = None

        # Create sizers for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # Record and Next buttons
        self.record_button = wx.Button(panel, label="Record")
        self.stop_button = wx.Button(panel, label="Stop")
        self.stop_button.Disable()  # Initially disable stop button

        self.text_ctrl = wx.StaticText(panel, label="Number of occurrences: 0", pos=(10, 10))

        panel_sizer.Add(self.record_button, 0, wx.ALL | wx.CENTER, 10)
        panel_sizer.Add(self.stop_button, 0, wx.ALL | wx.CENTER, 10)
        panel_sizer.Add(self.text_ctrl, 0, wx.ALL | wx.CENTER, 10)

        panel.SetSizer(panel_sizer)
        main_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 10)

        # Set main sizer and show dialog
        self.SetSizer(main_sizer)
        self.Fit()

        self.Bind(wx.EVT_BUTTON, self.on_record, self.record_button)  # Bind record button press event
        self.Bind(wx.EVT_BUTTON, self.on_stop, self.stop_button)  # Bind stop button press event

    def on_record(self, event):
        if not self.recording:
            self.recording = True
            self.stop_button.Enable()
            self.record_button.Disable()
            self.recording_thread = threading.Thread(target=send_recording,
                                                     args=(recording_file, "LongRecordPy", self.text_ctrl))
            self.recording_thread.start()

    def on_stop(self, event):
        if self.recording:
            sound_manager.stop_record()
            stop_record()
            print("Stopped recording")
            self.recording = False
            self.record_button.Enable()
            self.stop_button.Disable()
            wx.MessageBox("Stopped recording", "Info", wx.OK | wx.ICON_INFORMATION)


class SignupDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Sign Up", size=(400, 300))

        # Create sizers for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer = wx.BoxSizer(wx.VERTICAL)

        # Username label and text box
        username_label = wx.StaticText(self, label="Username:")
        self.username_text = wx.TextCtrl(self)  # Store as instance variable
        input_sizer.Add(username_label, 0, wx.ALL, 5)
        input_sizer.Add(self.username_text, 0, wx.EXPAND | wx.ALL, 5)

        # Password label and text box
        password_label = wx.StaticText(self, label="Password:")
        self.password_text = wx.TextCtrl(self, style=wx.TE_PASSWORD)  # Store as instance variable
        input_sizer.Add(password_label, 0, wx.ALL, 5)
        input_sizer.Add(self.password_text, 0, wx.EXPAND | wx.ALL, 5)

        # Password label and text box
        repassword_label = wx.StaticText(self, label="Confirm Password:")
        self.repassword_text = wx.TextCtrl(self, style=wx.TE_PASSWORD)  # Store as instance variable
        input_sizer.Add(repassword_label, 0, wx.ALL, 5)
        input_sizer.Add(self.repassword_text, 0, wx.EXPAND | wx.ALL, 5)

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
        repassword = self.repassword_text.GetValue()
        if not (password == "" or username == "" or repassword == ""):
            if re.search("[^0-9a-zA-Z]+", username) == username:
                if password == repassword:
                    if len(password) >= MINIMUM_PASSWORD_LENGTH:
                        message = signUp(username, password)
                        if message == "Sign up successful":
                            wx.MessageBox("Registered successfully", "Login Information", wx.OK | wx.ICON_INFORMATION)
                        elif message == "Username is in use":
                            wx.MessageBox("Username is already taken", "Login Information", wx.OK | wx.ICON_INFORMATION)
                        else:
                            wx.MessageBox("Registration failed", "Login Information", wx.OK | wx.ICON_INFORMATION)
                        self.EndModal(wx.ID_OK)
                    else:
                        wx.MessageBox("Password must be at least " + str(MINIMUM_PASSWORD_LENGTH) + " characters long",
                                      "Login Information",
                                      wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Password not matching", "Login Information",
                                  wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("Username can only contain numbers and letters", "Login Information",
                              wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Please enter all the fields", "Login Information",
                          wx.OK | wx.ICON_INFORMATION)


def signUp(username, password):
    message = "SignUp~" + username + "~" + password
    to_send = convert_with_length_prefix(message)
    send_receive_encrypted.send_encrypted(server_socket, to_send)
    return recv_by_size(server_socket).decode("utf-8")


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
    global server_socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            s.connect((HOST, PORT))
            send_receive_encrypted.set_encryption(s)
            server_socket = s

            app = wx.App()
            LoginDialog()
            app.MainLoop()
    except (ConnectionRefusedError, OSError) as e:
        print("Connection refused")


if __name__ == '__main__':
    main()
