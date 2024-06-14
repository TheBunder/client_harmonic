import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from tcp_by_size import send_with_size, recv_by_size

from hashlib import sha256
from math import ceil

import random

# Encryption variables
is_encrypted = False
iv_parms = ''
aes_key = ''


# def send_encrypted(sock, client_addr, to_send):
#     encrypt_cipher = AES.new(
#         CLIENTS_AES_INFO[client_addr][0], AES.MODE_CBC, CLIENTS_AES_INFO[client_addr][1]
#     )
#     to_send = encrypt_cipher.encrypt(pad(to_send, AES.block_size))
#     tcp_by_size.send_with_size(sock, b64encode(to_send))

def send_encrypted(sock, ba):
    cipher = AES.new(aes_key, AES.MODE_CBC, iv_parms)
    ba = pad(ba, AES.block_size)
    ba = cipher.encrypt(ba)
    ba = base64.b64encode(ba)
    print("send_encrypted", ba.decode())
    send_with_size(sock, ba)


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

# async def recv_decrypted(sock, client_addr):
#     decrypt_cipher = AES.new(
#         CLIENTS_AES_INFO[client_addr][0], AES.MODE_CBC, CLIENTS_AES_INFO[client_addr][1]
#     )
#     received = await tcp_by_size.recv_by_size(sock)
#     if received == b"":
#         return b""
#     original_data = unpad(
#         decrypt_cipher.decrypt(b64decode(received)), AES.block_size
#     )  # .decode().strip())  # Decrypt and then up-pad the result
#     return original_data
