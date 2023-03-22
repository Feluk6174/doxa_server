import binascii
import json
import auth
import time
import socket
from Crypto.Hash import SHA256
from typing import Union
import random
import threading


print("api", __name__)

class Connection():
    def __init__(self, host: str, port: int):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((host,  port))

        msg = '{"type": "CLIENT"}'
        self.connection.send(msg.encode("utf-8"))
        if self.connection.recv(1024).decode("utf-8") == "OK":
            print("[ESTABLISHED CONNECTION]", __name__)

        self.response_queue = []

        thread = threading.Thread(target=self.recv_queue)
        thread.start()

    def register_user(self, user_name:str, public_key, key_path:str, profile_picture:str, info:str):
        time_registered = int(time.time())
        public_key = auth.sanitize_key(public_key.export_key().decode("utf-8"))
        with open(key_path, "r") as f:
            keys_file = f.read()
        private_key = auth.sanitize_key(keys_file)
        pos = [random.randint(0,100) for _ in range(2)]
        print(pos)
        grup = 0
        msg = json.loads("{"+f'"type": "ACTION", "action": "REGISTER", "user_name": "{user_name}", "public_key": "{public_key}", "private_key": "{private_key}", "profile_picture": "{profile_picture}", "info": "{info}", "time": {time_registered}, "grup": {grup}, "pos": '+"{}}")
        msg["pos"] = {"pos": pos}
        msg = json.dumps(msg)
        print(msg)
        temp = self.send(msg)
        response = self.recv()
        if not response == "OK":
            if response == "ALREADY EXISTS":
                raise UserAlreadyExists(user_name)
            elif response == "WRONG CHARS":
                raise WrongCaracters(user_name=user_name, public_key=public_key, profile_picture=profile_picture, info=info, pos=pos)
            elif response == "DATABASE ERROR":
                raise DatabaseError(msg)

    def post(self, content:str, post_id:str, user_name:str, background_color:str, priv_key):
        with open("advanced_settings.json", "r") as f:
            advanced_options = json.loads(f.read())
        if advanced_options["encryption"]:
            if len(content) > 159:
                content = content[:159:]
            content = "[e] " + auth.encrypt(content)

        time_posted = int(time.time())
        signature = auth.sign(priv_key, content, post_id, user_name, background_color, time_posted).decode("utf-8")
        msg = "{"+f'"type": "ACTION", "action": "POST", "post_id": "{post_id}", "user_name": "{user_name}", "content": "{content}", "background_color": "{background_color}", "time": {time_posted}, "signature": "{signature}"'+"}"
        self.send(msg)
        response = self.recv()
        if not response == "OK":
            if response == "WRONG CHARS":
                raise WrongCaracters(user_name=user_name, public_key=content, profile_picture=post_id, info=background_color)
            elif response == "WRONG SIGNATURE":
                raise WrongSignature()
            elif response == "DATABASE ERROR":
                raise DatabaseError(msg)

    def change_profile_picture(self, user_name:str, profile_picture:str, priv_key):
        time_posted = int(time.time())
        signature = auth.sign(priv_key, user_name, profile_picture, time_posted).decode("utf-8")
        msg = "{"+f'"type": "ACTION", "action": "UPDATE PROFILE PICTURE", "user_name": "{user_name}", "profile_picture": "{profile_picture}", "time": {time_posted}, "signature": "{signature}"'+"}"
        self.send(msg)
        response = self.recv()
        if not response == "OK":
            if response == "WRONG CHARS":
                raise WrongCaracters(user_name=user_name, profile_picture=profile_picture)
            elif response == "WRONG SIGNATURE":
                raise WrongSignature()
            elif response == "DATABASE ERROR":
                raise DatabaseError(msg)

    def change_info(self, user_name:str, info:str, priv_key):
        time_posted = int(time.time())
        signature = auth.sign(priv_key, user_name, info, time_posted).decode("utf-8")
        msg = "{"+f'"type": "ACTION", "action": "UPDATE INFO", "user_name": "{user_name}", "info": "{info}", "time": {time_posted}, "signature": "{signature}"'+"}"
        self.send(msg)
        response = self.recv()
        if not response == "OK":
            if response == "WRONG CHARS":
                raise WrongCaracters(user_name=user_name, info=info)
            elif response == "WRONG SIGNATURE":
                raise WrongSignature()
            elif response == "DATABASE ERROR":
                raise DatabaseError(msg)

    def update_pos(self, user_name:str, pos:list, priv_key):
        time_posted = int(time.time())
        pos = '{'+f'"pos": {pos}'+'}'
        pos = pos.replace('"', '\\"')
        signature = auth.sign(priv_key, user_name, pos, time_posted).decode("utf-8")
        msg = "{"+f'"type": "ACTION", "action": "UPDATE POS", "user_name": "{user_name}", "pos": "{pos}", "time": {time_posted}, "signature": "{signature}"'+"}"
        self.send(msg)
        response = self.recv()
        if not response == "OK":
            if response == "WRONG CHARS":
                raise WrongCaracters(user_name=user_name, pos=pos)
            elif response == "WRONG SIGNATURE":
                raise WrongSignature()
            elif response == "DATABASE ERROR":
                raise DatabaseError(msg)

    def get_user_posts(self, user_name:str):
        #return format: {'id': 'str(23)', 'user_id': 'str(16)', 'content': 'str(255)', 'background_color': 'str(10)', 'time_posted': int}
        posts = []
        msg = "{"+f'"type": "ACTION", "action": "GET POSTS", "user_name": "{user_name}"'+"}"
        self.send(msg)
        num = int(self.recv())
        self.send('{"type": "RESPONSE", "response": "OK"}')
        if not num == 0: 
            for _ in range(num):
                posts.append(json.loads(self.recv()))
                self.send('{"type": "RESPONSE", "response": "OK"}')
            response = self.recv()
            if not response == "OK":
                if response == "WRONG CHARS":
                    raise WrongCaracters(user_name=user_name)

    def get_posts(self, sort_by:str = None, sort_order:str = None, user_name:Union[str, list] = None, hashtag:str = None, exclude_background_color:str = None, include_background_color:str = None, num:int = 10, offset:int = 0, id:Union[str, list] = None, grup:int = '"None"'):
        #return format: {'id': 'str(23)', 'user_id': 'str(16)', 'content': 'str(255)', 'background_color': 'str(10)', 'time_posted': int}
        posts = []
        if user_name == "" or user_name == []:
            f_user_name = '"No_posts_1"'
        elif type(user_name) == str:
            f_user_name = f'"{user_name}"'
        elif type(user_name) == list:
            f_user_name = '"'
            for u_name in user_name:
                f_user_name += u_name + ","
            f_user_name = f_user_name[:-1] +'"'
        else:
            f_user_name = '"None"'

        if id == "" or id == []:
            f_id = '"0"'
        elif type(id) == str:
            f_id = f'"{user_name}"'
        elif type(id) == list:
            f_id = '"'
            for i in id:
                f_id += i + ","
            f_id = f_id[:-1] +'"'
        else:
            f_id = '"None"'
        

        msg = "{"+f'"type": "ACTION", "action": "GET POSTS", "user_name": {f_user_name}, "hashtag": "{hashtag}", "include_background_color": "{include_background_color}", "exclude_background_color":"{exclude_background_color}", "sort_by": "{sort_by}", "sort_order": "{sort_order}", "num": "{num}", "offset": "{offset}", "id": {f_id}, "grup": {grup}'+"}"
        print(msg)
        self.send(msg)
        num = int(self.recv())
        print(num)
        self.send('{"type": "RESPONSE", "response": "OK"}')
        if not num == 0: 
            with open("user_keys.json", "r") as f:
                keys = json.loads(f.read())
                for _ in range(num):
                    post = json.loads(self.recv())
                    try:
                        if post["content"][:3:] == "[e]":
                            post["content"] = auth.decrypt(post["content"][4::], keys[post["user_id"]].encode("utf-8"))
                        else:
                            post["content"] = auth.decrypt(post["content"], keys[post["user_id"]].encode("utf-8"))
                    except (KeyError, binascii.Error, ValueError):
                        if post["content"][:3:] == "[e]":
                            post["content"] = "[ENCRYPTED]"
                    posts.append(post)
                    self.send('{"type": "RESPONSE", "response": "OK"}')
                response = self.recv()
                if not response == "OK":
                    if response == "WRONG CHARS":
                        raise WrongCaracters(user_name=user_name)

            return posts
        response = self.recv()
        if not response == "OK":
            if response == "WRONG CHARS":
                print(user_name)
                raise WrongCaracters(user_name=user_name)
        return [{}]
        
    def get_user(self, user_name:str):
        msg = "{"+f'"type": "ACTION", "action": "GET USER", "user_name": "{user_name}"'+"}"
        print(msg)
        self.send(msg)
        response = self.recv()

        try:
            return json.loads(response)
        except json.decoder.JSONDecodeError:
            if response == "WRONG CHARS":
                raise WrongCaracters(user_name=user_name)
            return {}

    def close(self):
        self.connection.close()

    def get_post(self, post_id:str):
        msg = "{"+f'"type": "ACTION", "action": "GET POST", "post_id": "{post_id}"'+"}"
        self.send(msg)
        response = self.recv()
        try:
            return json.loads(response)
        except json.decoder.JSONDecodeError:
            if response == "WRONG CHARS":
                raise WrongCaracters(post_id=post_id)
            return {}

    def send(self, msg:str):
        msg_len = len(msg)
        msg_id = SHA256.new(msg.encode("utf-8")).hexdigest()

        num = int(msg_len/512)
        num = num + 1 if not msg_len % 512 == 0 else num
        
        send_msg = "{"+f'"type": "NUM", "num": {num}, "id": "{msg_id}"'+"}"
        temp = self.connection.send(send_msg.encode("utf-8"))

        temp = json.loads(self.recv_from_queue())
        temp = temp["response"]
        if not temp == "OK":
            print("S1" + str(temp))

        for i in range(num):
            msg_part = msg[512*i:512*i+512].replace("\"", '\\"')
            send_msg = "{"+f'"type": "MSG PART", "id": "{msg_id}", "content": "{msg_part}"'+"}"
            self.connection.send(send_msg.encode("utf-8"))
            temp = self.recv_from_queue()
            temp = json.loads(temp)
            temp = temp["response"]
            if not temp == "OK":
                print("S2" + str(temp))


    def recv(self):
        data = json.loads(self.recv_from_queue())
        num = data["num"]
        msg_id = data["id"]
        response = "{"+f'"type": "CONN RESPONSE", "response": "OK", "id": "{msg_id}"'+"}"
        self.connection.send(response.encode("utf-8"))
        msg = ""
        for i in range(num):
            msg += json.loads(self.recv_from_queue())["content"]
            self.connection.send(response.encode("utf-8"))

        return msg

    def recv_queue(self):
        self.run = True
        while self.run:
            temp = self.connection.recv(1024).decode("utf-8")
            temp = "}\0{".join(temp.split("}{")).split("\0")

            if "stop" in temp:
                break

            for msg in temp:
                self.response_queue.append(msg)
        else:
            print(1)
        print("closed thread")

    def recv_from_queue(self):
        while True:
            if not len(self.response_queue) == 0:
                temp = self.response_queue[0]
                self.response_queue.pop(0)
                return temp





def check_chars(*args):
    invalid_chars = ["\\", "\'", "\n", "\t", "\r", "\0", "%", "\b", ";", "=", "\u259e"]

    arguments = ""
    for argument in args:
        arguments += str(argument)


    for i, char in enumerate(invalid_chars):
        if char in arguments:
            return False, char
    return True, None




class UserAlreadyExists(Exception):
    def __init__(self, user_name):
        self.message = f"User {user_name} already exists"
        super().__init__(self.message)

class WrongCaracters(Exception):
    def __init__(self, **kwargs):
        self.message = "wtf"
        for key, value in kwargs.items():
            check, char = check_chars(str(value))
            if not check:
                self.message = f"{key}(value = {value}) contains the character {char}"
                
        super().__init__(self.message)

class WrongSignature(Exception):
    def __init__(self, **kwargs: object):
        super().__init__("key verification failed")

class DatabaseError(Exception):
    def __init__(self, request):
        super().__init__(f"The request '{request}' caused a database error")
