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
                if msg == "":
                    raise socket.error

                # if the client sent t many messages to fast, they can all arribe at in the same connection.recv()
                # whith ithis we split it into ts parts
                msgs = msg.replace("}{", "}\0{").split("\0")

                # in this loop the messages are rebuilt
                for msg in msgs:
                    msg = json.loads(msg)
                    
                    # in this part the server sees the amount of pparts the message will come from
                    # and the id thet will identify them, and stores that in a dict, which contains a dict
                    # which contains the the content (at the start it is empty), the num of parts that have to come
                    # and the num of prts that alredy came
                    if msg["type"] == "NUM" and not msg["num"] == 0:
                        self.temp_msgs[msg["id"]] = {"content": "", "num": msg["num"], "act_num": 0}
                        send_msg = "{"+f'"type": "CONN RESPONSE", "response": "OK", "id": "{msg["id"]}"'+"}"
                        self.connection.send(send_msg.encode("utf-8"))

                    # this prossesed a part of a message
                    # first it append the content to the dict anth then adds one to the amoun of parts that have arried
                    # then it checks if all parts have arribed
                    # if it has t loads the content to a dict
                    # then depending on the type it is added to the queue (self.queue) or the reponses queue (self.responses)
                    # then it sends confimation to theclient
                    if msg["type"] == "MSG PART":
                        self.temp_msgs[msg["id"]]["content"] += msg["content"]
                        self.temp_msgs[msg["id"]]["act_num"] += 1

                        if self.temp_msgs[msg["id"]]["num"] == self.temp_msgs[msg["id"]]["act_num"]:
                            res_msg = json.loads(self.temp_msgs[msg["id"]]["content"])
                            if res_msg["type"] == "ACTION":
                                self.queue.append(res_msg)
                            elif res_msg["type"] == "RESPONSE":
                                self.responses.append(res_msg)
                        send_msg = "{"+f'"type": "CONN RESPONSE", "response": "OK", "id": "{msg["id"]}"'+"}"
                        self.connection.send(send_msg.encode("utf-8"))
                    
                    # if the the response is for the slf.send function, it is added to the the corresponding queue
                    if msg["type"] == "CONN RESPONSE":
                        self.send_responses.append(msg)

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

                elif msg_info["action"] == "GET POST":
                    user_actions.get_post(msg_info, self)
                
                elif msg_info["action"] == "UPDATE PROFILE PICTURE":
                    user_actions.change_profile_picture(msg_info, self)

                elif msg_info["action"] == "UPDATE INFO":
                    user_actions.change_info(msg_info, self)

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
                if msg == "":
                    raise socket.error
                
                # if the client sent t many messages to fast, they can all arribe at in the same connection.recv()
                # whith ithis we split it into ts parts
                msgs = msg.replace("}{", "}\0{").split("\0")
                
                # in this loop the messages are rebuilt
                for msg in msgs:
                    msg = json.loads(msg)
                    logger.log("msg", msg)

                    # in this part the server sees the amount of pparts the message will come from
                    # and the id thet will identify them, and stores that in a dict, which contains a dict
                    # which contains the the content (at the start it is empty), the num of parts that have to come
                    # and the num of prts that alredy came
                    if msg["type"] == "NUM" and not msg["num"] == 0:
                        self.temp_msgs[msg["id"]] = {"content": "", "num": msg["num"], "act_num": 0}
                        send_msg = "{"+f'"type": "CONN RESPONSE", "response": "OK", "id": "{msg["id"]}"'+"}"
                        self.connection.send(send_msg.encode("utf-8"))

                    # this prossesed a part of a message
                    # first it append the content to the dict anth then adds one to the amoun of parts that have arried
                    # then it checks if all parts have arribed
                    # if it has t loads the content to a dict
                    # then depending on the type it is added to the queue (self.queue) or the reponses queue (self.responses)
                    # then it sends confimation to the client
                    if msg["type"] == "MSG PART":
                        self.temp_msgs[msg["id"]]["content"] += msg["content"]
                        self.temp_msgs[msg["id"]]["act_num"] += 1

                        if self.temp_msgs[msg["id"]]["num"] == self.temp_msgs[msg["id"]]["act_num"]:
                            res_msg = json.loads(self.temp_msgs[msg["id"]]["content"])
                            if res_msg["type"] == "ACTION":
                                self.queue.append(res_msg)
                            elif res_msg["type"] == "RESPONSE":
                                self.responses.append(res_msg)
                        send_msg = "{"+f'"type": "CONN RESPONSE", "response": "OK", "id": "{msg["id"]}"'+"}"
                        self.connection.send(send_msg.encode("utf-8"))
                    
                    # if the the response is for the slf.send function, it is added to the the corresponding queue
                    if msg["type"] == "CONN RESPONSE":
                        logger.log("queueing", msg)
                        self.send_responses.append(msg)

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

    logger.stop()
    logger = get_logger
    clients = get_clients
    connections = get_connections
    db.stop()
    db = get_db

logger = log.Logger(None)
clients = []
connections = []
db = database.Database()

import user_actions