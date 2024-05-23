import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
from tcp_by_size import send_with_size, recv_by_size


# def send_encrypted(sock, client_addr, to_send):
#     encrypt_cipher = AES.new(
#         CLIENTS_AES_INFO[client_addr][0], AES.MODE_CBC, CLIENTS_AES_INFO[client_addr][1]
#     )
#     to_send = encrypt_cipher.encrypt(pad(to_send, AES.block_size))
#     tcp_by_size.send_with_size(sock, b64encode(to_send))

def send_encrypted(sock, ba, aes_key, iv_parms):
    cipher = AES.new(aes_key, AES.MODE_CBC, iv_parms)
    ba = pad(ba, AES.block_size)
    ba = cipher.encrypt(ba)
    ba = base64.b64encode(ba)
    print("send_encrypted", ba.decode())
    send_with_size(sock, ba)



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
