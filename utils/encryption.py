

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

def encrypt(data_to_encrypt, key):
    padded_data = padding_text(data_to_encrypt)
    pad_len = len(padded_data) - len(data_to_encrypt)
    bpad = pad_len.to_bytes(4, 'big')
    cipher = AES.new(key, AES.MODE_CBC)
    ciphtertext = cipher.iv + bpad + cipher.encrypt(padded_data)
    return ciphtertext

def decrypt(ciphertext, key):
    cipher = AES.new(key, AES.MODE_CBC, iv=ciphertext[:16])
    bpad = ciphertext[16:20]
    pad = int.from_bytes(bpad, 'big')
    msg = cipher.decrypt(ciphertext[20:])
    # msg = msg[0:-pad]
    return msg

def encrypt_file(filename, key):
    with open(filename, 'rb') as f:
        data = f.read()
        if data != b'':
            return encrypt(data, key)
    return None

def decrypt_file(ciphertext, key, filename):
    data = decrypt(ciphertext, key)
    print(len(data))
    with open(filename, 'wb') as f:
        f.write(data)

