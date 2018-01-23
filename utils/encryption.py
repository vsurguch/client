

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES, PKCS1_OAEP


#server
def generate_key_public_key():
    key = RSA.generate(1024)
    public = key.publickey()
    return key, public

def generate_cipher_rsa_private(key):
    return PKCS1_OAEP.new(key)

#client
def generate_cipher_rsa(public_key):
    public_key = RSA.import_key(public_key)
    return PKCS1_OAEP.new(public_key)

def generate_session_key(cipher_rsa, session_key):
    return cipher_rsa.encrypt(session_key)

#both
def padding_text(text):
    pad_len = (16 - len(text) % 16) % 16
    return text + b' ' * pad_len

def encrypt(plaintext, key):
    cipher = AES.new(key, AES.MODE_CBC)
    ciphtertext = cipher.iv + cipher.encrypt(plaintext)
    return ciphtertext

def decrypt(ciphertext, key):
    cipher = AES.new(key, AES.MODE_CBC, iv=ciphertext[:16])
    msg = cipher.decrypt(ciphertext[16:])
    return msg
