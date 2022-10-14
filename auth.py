from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
import base64
from Crypto.Signature import pss
from Crypto.Hash import SHA256

def gen_key(passphrase):
    key = RSA.generate(2048)
    encrypted_key = key.export_key(passphrase=passphrase, pkcs=8,
                                  protection="scryptAndAES128-CBC")

    with open("rsa_key.bin", "wb") as f:
        f.write(encrypted_key)


def get_keys(passphrase):
    with open("rsa_key.bin", "rb") as f:
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
    with open("rsa_key.bin", "wb") as f:
        f.write(priv_key.encode("utf-8"))
    try:
        get_keys(password)
    except ValueError:
        return False
    
    return True