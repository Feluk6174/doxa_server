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
    def __init__(self, host: str=None, port: int=None):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.response_queue = []
        self.read = 0
        self.size = 0
        self.message = ""

        self.queue_started = False

        thread = threading.Thread(target=self.recv_queue)

        msg = '{"type": "CLIENT"}'
        
        if not host == None:
            self.connection.connect((host,  port))
            self.connection.send(msg.encode("utf-8"))
            if self.connection.recv(1024).decode("utf-8") == "OK":
                print("[ESTABLISHED CONNECTION]", __name__)
                self.queue_started = True

            thread.start()

            with open("ips.ips", "w") as f:
                f.write(json.dumps({"ips": self.get_ips()}))
        else:
            connected = False
            final_ips = {"ips": []}
            with open("ips.ips", "r") as f:
                ips = json.loads(f.read())["ips"]
            for ip in ips:
                try:
                    ip = ip.split(":")
                    host = ip[0]
                    port = int(ip[1])
                    self.connection.connect((host,  port))
                    self.connection.send(msg.encode("utf-8"))
                    if self.connection.recv(1024).decode("utf-8") == "OK":
                        print("[ESTABLISHED CONNECTION]", __name__)
                        self.queue_started = True
                    final_ips["ips"].append(":".join(ip))
                    connected = True
                    thread.start()

                    break
                except ConnectionRefusedError:
                    pass
                except OSError:
                    pass
            if not connected:
                self.connection.connect(("34.175.220.44",  30003))
                self.connection.send(msg.encode("utf-8"))
                if self.connection.recv(1024).decode("utf-8") == "OK":
                    print("[ESTABLISHED CONNECTION]", __name__)
                    self.queue_started = True
                final_ips["ips"].append("34.175.220.44:30003")
            
            # start thread to be able to get self.get_ips()
            thread.start()
            final_ips["ips"].extend(self.get_ips())
            with open("ips.ips", "w") as f:
                f.write(json.dumps({"ips": final_ips}))
        
        
        

    def register_user(self, user_name:str, public_key, key_path:str, profile_picture:str, info:str):
        time_registered = int(time.time())
        public_key = auth.sanitize_key(public_key.export_key().decode("utf-8"))
        with open(key_path, "r") as f:
            keys_file = f.read()
        private_key = auth.sanitize_key(keys_file)
        pos = [float(random.randint(0,100)) for _ in range(2)]
        print(pos)
        grup = 0
        msg = json.loads("{"+f'"type": "ACTION", "action": "REGISTER", "user_name": "{user_name}", "public_key": "{public_key}", "private_key": "{private_key}", "profile_picture": "{profile_picture}", "info": "{info}", "time": {time_registered}, "grup": {grup}, "pos": '+"{}}")
        msg["pos"] = {"pos": pos}
        msg = json.dumps(msg)
        print("msg1:", msg)
        temp = self.send(msg)
        response = self.recv()
        if not response == "OK":
            if response == "ALREADY EXISTS":
                raise UserAlreadyExists(user_name)
            elif response == "WRONG CHARS":
                raise WrongCaracters(user_name=user_name, public_key=public_key, profile_picture=profile_picture, info=info, pos=pos, msg=msg)
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

    def update_pos(self, user_name:str, pos:list[float], priv_key):
        pos = {"pos": pos}
        time_posted = int(time.time())
        signature = auth.sign(priv_key, user_name, pos, time_posted).decode("utf-8")
        msg = "{"+f'"type": "ACTION", "action": "UPDATE POS", "user_name": "{user_name}", "pos": '+'{}'+f', "time": {time_posted}, "signature": "{signature}"'+"}"
        msg = json.loads(msg)
        msg["pos"] = pos
        msg = json.dumps(msg)
        print("msg2:", msg)
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

    def get_posts(self, sort_by:str = None, sort_order:str = None, user_name:Union[str, list[str]] = None, hashtag:str = None, exclude_background_color:str = None, include_background_color:str = None, num:int = 10, offset:int = 0, id:Union[str, list[str]] = None, grup:int = '"None"'):
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
            f_id = f'"{id}"'
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
        except json.decoder.JSONDecodeError as e:
            print(e)
            if response == "WRONG CHARS":
                raise WrongCaracters(user_name=user_name)
            return {}

    def get_users(self, user_names:list[str]):
        users = ",".join(user_names)
        msg = "{"+f'"type": "ACTION", "action": "GET USERS", "user_names": "{users}"'+"}"
        print(msg)
        self.send(msg)
        num = int(self.recv())
        self.send('{"type": "RESPONSE", "response": "OK"}')
        posts = []
        if not num == 0:
            for _ in range(num):
                post = json.loads(self.recv())
                posts.append(post)
                self.send('{"type": "RESPONSE", "response": "OK"}')
            return posts
        response = self.recv()
        if not response == "OK":
            if response == "WRONG CHARS":
                print(user_names)
                raise WrongCaracters(user_name=user_names)
        return [{}]

    def get_ips(self):
        msg = '{"type": "ACTION", "action": "GET IPS"}'
        print(msg)
        self.send(msg)
        response = self.recv()

        try:
            return json.loads(response)["ips"]
        except json.decoder.JSONDecodeError as e:
            print(e)
            if response == "WRONG CHARS":
                raise WrongCaracters(msg=msg)
            return []

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

    def send(self, data:str):
        bdata = data.encode("utf-8")
        lenghth = str(len(bdata))
        lenghth = ("0"*(8-len(lenghth))+lenghth).encode("utf-8")
        bdata = lenghth+bdata
        self.connection.send(bdata)


    def recv_queue(self):
        print("started queue")
        self.run = True
        while True:
            if True:
                msg = self.connection.recv(1024).decode("utf-8")
                print(msg)
                if msg == "":
                    raise socket.error

                for char in msg:
                    # The first 8 bytes of a message indicate the size of it
                    # This calculates the size of the message
                    if self.read < 8:
                        self.size += int(char)*(10**(7-self.read))
                    else:
                        self.message += char
                    
                    if self.read == self.size+7 and not self.read == 0:
                        self.read = 0
                        self.size = 0
                        self.response_queue.append(self.message)
                        self.message = ""
                    else:
                        self.read += 1
            #except:
            #    pass
        else:
            print(1)
        print("closed thread")

    def recv(self):
        while True:
            if not len(self.response_queue) == 0:
                temp = self.response_queue[0]
                self.response_queue.pop(0)
                return temp





def check_chars(*args):
    invalid_chars = ["\\", "\'", "\n", "\t", "\r", "\0", "%", "\b", ";", "\u259e"]

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
