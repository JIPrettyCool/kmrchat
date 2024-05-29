import socket
import threading
import curses
import base64
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def derive_key(password):
    salt = b'\x00' * 16
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_message(key, plaintext):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode()

def decrypt_message(key, ciphertext):
    ciphertext = base64.b64decode(ciphertext.encode())
    iv = ciphertext[:16]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext[16:]) + decryptor.finalize()
    return plaintext.decode()

def receive_messages(stdscr, client_socket, key):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            decrypted_message = decrypt_message(key, message)
            stdscr.addstr(decrypted_message + "\n")
            stdscr.refresh()
        except:
            break

def main(stdscr):
    curses.curs_set(0)
    stdscr.clear()

    stdscr.addstr("Enter your nickname: ")
    stdscr.refresh()
    nickname = stdscr.getstr().decode()

    stdscr.clear()
    stdscr.addstr("Enter channel name: ")
    stdscr.refresh()
    channel_name = stdscr.getstr().decode()
    key = derive_key(channel_name)

    stdscr.clear()
    stdscr.addstr("Connecting...\n")
    stdscr.refresh()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 5555))

    stdscr.clear()
    stdscr.addstr("Connected! Type your messages below:\n")
    stdscr.refresh()

    threading.Thread(target=receive_messages, args=(stdscr, client_socket, key)).start()

    input_win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
    input_win.refresh()

    while True:
        input_win.clear()
        stdscr.refresh()
        curses.echo()
        try:
            message = input_win.getstr().decode()
            full_message = f"{nickname}: {message}"
            encrypted_message = encrypt_message(key, full_message)
            client_socket.send(encrypted_message.encode())

            stdscr.addstr(f"{nickname}: {message}\n")
            stdscr.refresh()
        except:
            break

if __name__ == "__main__":
    import platform
    if platform.system() == "Windows":
        import os
        os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main)
