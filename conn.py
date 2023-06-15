import socket
import threading
import json
import time
from Crypto.Hash import SHA256

import database
import log
import managment

class ClientConnection():
    def __init__(self, connection:socket.socket, conn_info:dict):
        # sets up a the object of the client connection
        # takes a connection(connection), a socket.socket object, and the information of the connection(conn_info), a dict
        # also sstarts a thread to proses the queue(self.process_queue)
        logger.log("client")
        self.connection = connection
        self.info = conn_info
        self.queue = []
        self.responses = []
        self.temp_msgs = {}
        self.send_responses = []
        self.ip = None
        self.read = 0
        self.size = 0
        self.message = ""

        thread = threading.Thread(target=self.process_queue)
        thread.start()

    def manage_requests(self):
        # function thaat manages requests
        # when the client seends a message, the message is prossesed by this function
        # in this function the messages are reassembled and sent to the corresponding queue
        global clients, logger
        while True:
            try:
                msg = self.connection.recv(1024).decode("utf-8")
                logger.log(msg)
                if msg == "":
                    raise socket.error
                    
                if not msg[0] in "0123456789":
                    self.connection.close()
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
                        message_dict:dict = json.loads(self.message)
                        if message_dict["type"] == "ACTION":
                            self.queue.append(message_dict)
                        elif message_dict["type"] == "RESPONSE":
                            self.responses.append(message_dict)
                        self.message = ""
                    else:
                        self.read += 1

                

            # if there is a socket error, which can be caused by a client disconecting or the internet going out 
            # the error will be logged, then the client will be removed from thee clients list
            # and a command will be sent to kill the queue porrseor (self.prosses_queue)
            except socket.error as e:
                logger.log("[ERROR]" + str(e))
                clients.remove(self)
                self.queue.append("kill")
                break
            
            # if a jason that doesent work is sent, whch can be caused by a client cosing the connection
            # an errorin the splitinng of parts, or an error in the client
            # the error will be logged, then the client will be removed from thee clients list
            # and a command will be sent to kill the queue porrseor (self.prosses_queue)
            except json.decoder.JSONDecodeError as e:
                logger.log("[ERROR]" + str(e) + " " + str(msg))
                clients.remove(self)
                self.queue.append("kill")
                break

    def process_queue(self):
        global logger
        logger.log("client queue")
        while True:
            if "kill" in self.queue:
                break
            if not len(self.queue) == 0:
                msg_info = self.queue[0]
                logger.log(f"recived: {msg_info} {type(msg_info)}")

                if msg_info["action"] == "REGISTER":
                    user_actions.register_user(msg_info, self)

                elif msg_info["action"] == "POST":
                    user_actions.new_post(msg_info, self)

                elif msg_info["action"] == "GET POSTS":
                    user_actions.get_posts(msg_info, self)

                elif msg_info["action"] == "GET USER":
                    user_actions.get_user_info(msg_info, self)

                elif msg_info["action"] == "GET USERS":
                    user_actions.get_users_info(msg_info, self)

                elif msg_info["action"] == "GET POST":
                    user_actions.get_post(msg_info, self)
                
                elif msg_info["action"] == "GET IPS":
                    user_actions.get_ips(msg_info, self)
                
                elif msg_info["action"] == "UPDATE PROFILE PICTURE":
                    user_actions.change_profile_picture(msg_info, self)

                elif msg_info["action"] == "UPDATE INFO":
                    user_actions.change_info(msg_info, self)

                elif msg_info["action"] == "UPDATE POS":
                    user_actions.update_pos(msg_info, self)

                elif msg_info["action"] == "SEND":
                    self.send(msg_info["msg"])

                self.queue.pop(0)

    def recv_from_queue(self):
        global logger
        while True:
            if not len(self.responses) == 0:
                res = self.responses[0]
                self.responses.pop(0)
                return res

    def recv_send_response(self, msg_id:str):
        global logger
        while True:
            if not len(self.send_responses) == 0:
                for i, response in enumerate(self.send_responses):
                    if response["id"] == msg_id:
                        res = response["response"]
                        self.send_responses.pop(i)
                        return res


    def send(self, msg:str):
        global logger
        bmsg = msg.encode("utf-8")
        logger.log("sending: "+msg)    
        lenghth = str(len(bmsg))
        lenghth = ("0"*(8-len(lenghth))+lenghth).encode("utf-8")
        bmsg = lenghth+bmsg
        logger.log("sent", bmsg)
        self.connection.send(bmsg)


class NodeConnection():
    def __init__(self, connection:socket.socket, conn_info:dict, address:str):
        # setsup a the object of the client connection
        # takes a connection(connection), a socket.socket object, and the information of the connection(conn_info), a dict
        # annd inialitzes all the needed variables
        # also sstarts a thread to proses the queue(self.process_queue)
        self.connection = connection
        self.info = conn_info
        self.queue = []
        self.responses = []
        self.send_responses = []
        self.temp_msgs = {}
        self.ip = self.info["ip"]
        self.real_ip = address
        self.read = 0
        self.size = 0
        self.message = ""

        global logger 
        logger.log("connected by", self.ip)

        thread = threading.Thread(target=self.process_queue)
        thread.start()

    def manage_requests(self):
        # function thaat manages requests
        # when the client seends a message, the message is prossesed by this function
        # in this function the messages are reassembled and sent to the corresponding queue
        global connections, logger
        while True:
            try:
                msg = self.connection.recv(1024).decode("utf-8")
                logger.log(msg)
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
                        message_dict:dict = json.loads(self.message)
                        if message_dict["type"] == "ACTION":
                            self.queue.append(message_dict)
                        elif message_dict["type"] == "RESPONSE":
                            self.responses.append(message_dict)
                        self.message = ""
                    else:
                        self.read += 1

            except socket.error as e:
                logger.log("[ERROR]" + str(e))
                connections.remove(self)
                self.queue.append("kill")
                break

            except json.decoder.JSONDecodeError as e:
                logger.log("[ERROR]" + str(e) + " " + str(msg))
                connections.remove(self)
                self.queue.append("kill")
                break

    def process_queue(self):
        global logger
        while True:
            if "kill" in self.queue:
                break
            if not len(self.queue) == 0:
                msg_info = self.queue[0]
                logger.log(f"recived: {msg_info} {type(msg_info)}")
                if msg_info["action"] == "IP":
                    managment.manage_ip(msg_info, self.ip)

                if msg_info["action"] == "REGISTER":
                    user_actions.register_user(msg_info, self, ip=self.ip)

                if msg_info["action"] == "POST":
                    user_actions.new_post(msg_info, self, ip=self.ip)

                elif msg_info["action"] == "UPDATE PROFILE PICTURE":
                    user_actions.change_profile_picture(msg_info, self, ip=self.ip)

                elif msg_info["action"] == "UPDATE INFO":
                    user_actions.change_info(msg_info, self, ip=self.ip)

                elif msg_info["action"] == "UPDATE POS":
                    user_actions.update_pos(msg_info, self, ip=self.ip)

                elif msg_info["action"] == "EXPORT":
                    managment.export_db(self)

                elif msg_info["action"] == "IMPORT":
                    managment.import_db(self)

                if msg_info["action"] == "SEND":
                    self.send(msg_info["msg"])

                n_connected = len(connections)
                n_nodes = len(db.querry("SELECT * FROM ips;"))
                n_suposed_connections = managment.get_suposed_connected(n_nodes)
                if n_connected < n_suposed_connections:
                    thread = threading.Thread(target=managment.connect_to_new_node)
                    thread.start()


                self.queue.pop(0)
    

    def recv_from_queue(self):
        global logger
        while True:
            if not len(self.responses) == 0:
                res = self.responses[0]
                self.responses.pop(0)
                return res

    def recv_send_response(self, msg_id:str):
        global logger
        while True:
            if not len(self.send_responses) == 0:
                for i, response in enumerate(self.send_responses):
                    if response["id"] == msg_id:
                        res = response["response"]
                        self.send_responses.pop(i)
                        return res


    def recv_from_queue(self):
        while True:
            if not len(self.responses) == 0:
                res = self.responses[0]
                self.responses.pop(0)
                return res

    def recv_send_response(self, msg_id:str):
        global logger
        while True:
            if not len(self.send_responses) == 0:
                for i, response in enumerate(self.send_responses):
                    if response["id"] == msg_id:
                        res = response["response"]
                        self.send_responses.pop(i)
                        return res


    def send(self, msg:str):
        global logger
        bmsg = msg.encode("utf-8")
        logger.log("sending: "+msg)    
        lenghth = str(len(bmsg))
        lenghth = ("0"*(8-len(lenghth))+lenghth).encode("utf-8")
        bmsg = lenghth+bmsg
        logger.log("sent", bmsg)
        self.connection.send(bmsg)

    def send(self, msg:str):
        global logger
        logger.log("sending: "+msg)
        msg_len = len(msg)
        msg_id = SHA256.new(msg.encode("utf-8")).hexdigest()

        num = int(msg_len/512)
        num = num + 1 if not msg_len % 512 == 0 else num
        send_msg = "{"+f'"type": "NUM", "num": {num}, "id": "{msg_id}"'+"}"
        temp = self.connection.send(send_msg.encode("utf-8"))

        temp = self.recv_send_response(msg_id)
        if not temp == "OK":
            logger.log("S1" + str(temp))

        for i in range(num):
            msg_part = msg[512*i:512*i+512].replace("\"", '\\"')
            send_msg = "{"+f'"type": "MSG PART", "id": "{msg_id}", "content": "{msg_part}"'+"}"
            self.connection.send(send_msg.encode("utf-8"))
            temp = self.recv_send_response(msg_id)
            if not temp == "OK":
                logger.log("S2" + str(temp))


def init(get_logger:log.Logger, get_clients:list, get_connections:list, get_db:database.Database):
    # sets global variables 
    # logger(log.Logger), 
    # clients(list, which contains conn.ClientConnection), 
    # connections(list, which contains conn.NodeConnections) and 
    # db(database.Database)
    global logger, clients, connections, db

    logger = get_logger
    clients = get_clients
    connections = get_connections
    db = get_db

logger = log.Logger(None, real=False)
clients = []
connections = []
db = database.Database(real=False)

import user_actions