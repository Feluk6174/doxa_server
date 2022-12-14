from Crypto.PublicKey import RSA
import base64
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad
import string    
import random 

def gen_key(passphrase):
    key = RSA.generate(2048)
    encrypted_key = key.export_key(passphrase=passphrase, pkcs=8,
                                  protection="scryptAndAES128-CBC")

    with open("./rsa_key.bin", "wb") as f:
        f.write(encrypted_key)


def get_keys(passphrase):
    with open("./rsa_key.bin", "rb") as f:
        encoded_key = f.read()
        key = RSA.import_key(encoded_key, passphrase=passphrase)
        pub_key = key.publickey()
        return key, pub_key

def gen_hash(*args):
    message = ""
    for arg in args:
        message += str(arg)
    return SHA256.new(message.encode("utf-8"))

def sanitize_key(key:str):
    clean_str = ""
    
    for i, line in enumerate(key.split("\n")):
        if not i == 0 and not i == len(key.split("\n"))-1:
            clean_str += line

    return clean_str


def reconstruct_key(sanitized_key, key_type="priv"):
    key = ""
    i = 0
    if key_type == "priv":
        key += "-----BEGIN ENCRYPTED PRIVATE KEY-----\n"
    elif key_type == "pub":
        key += "-----BEGIN PUBLIC KEY-----\n"
    num = int(len(sanitized_key)/64)
    for i in range(num):
        key += sanitized_key[i*64:i*64+64]+"\n"
    key += sanitized_key[(i+1)*64::]+"\n"
    
    if key_type == "priv":
        key += "-----END ENCRYPTED PRIVATE KEY-----"
    elif key_type == "pub":
        key += "-----END PUBLIC KEY-----"
    
    return key


def sign(key, *args):
    h = gen_hash(*args)
    signature = pss.new(key).sign(h)
    return base64.urlsafe_b64encode(signature)

def verify(pub_key, signature, *args):
    signature = base64.urlsafe_b64decode(signature)
    h = gen_hash(*args)
    verifier = pss.new(pub_key)
    verifier.verify(h, signature)    
    try:
        verifier.verify(h, signature)
        return True


    except (ValueError, TypeError) as e:
        print("[ERROR]", e)
        return False

def login(priv_key:str, password:str):
    priv_key = reconstruct_key(priv_key)
    with open("./rsa_key.bin", "w") as f:
        f.write(priv_key)
    try:
        get_keys(password)
    except ValueError:
        return False
    return True

def gen_aes_key():
    with open("aes_key.bin", "wb") as f:
        key = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k = 32))  
        f.write(key.encode("ascii"))   
    
def get_aes_key():
    with open("aes_key.bin", "rb") as f:
        key = f.read()
    return key

def encrypt(data:str):
    from Crypto.Cipher import AES

    key = get_aes_key()
    cipher = AES.new(key, AES.MODE_CBC) # Create a AES cipher object with the key using the mode CBC
    ciphered_data = cipher.encrypt(pad(data.encode("utf-8"), AES.block_size)) 
    ciphertext = cipher.iv + ciphered_data
    print("aes1", cipher.iv, ciphered_data, ciphertext)
    return base64.b64encode(ciphertext).decode("utf-8")
    

def decrypt(ciphertext, key):
    print("owo", len(ciphertext), ciphertext)
    ciphertext = base64.b64decode(ciphertext.encode("utf-8"))
    iv = ciphertext[:16:]
    ciphered_data = ciphertext[16::]

    print("aes2", iv, ciphered_data, ciphertext)

    print("uwu", iv, len(iv), type(iv), ciphered_data, len(ciphered_data), type(ciphered_data))

    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext = unpad(cipher.decrypt(ciphered_data), AES.block_size)
    print(type(plaintext))
    return plaintext.decode("utf-8")

