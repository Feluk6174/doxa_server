import time
import json
import socket
import threading
import math

import log
import database
import recomendation
from conn import NodeConnection, ClientConnection
from typing import Union

def import_db(connection:NodeConnection):
    global db
    connection.send('{"type": "ACTION", "action": "EXPORT"}')
    commands = connection.recv_from_queue()["response"].replace("\u259f", "\'").split("\u259e")
    if "" in commands:
        commands.remove("")
    db.import_db(commands)

def export_db(connection:NodeConnection):
    global db

    text = ""

    users = db.querry("SELECT * FROM users;")
    posts = db.querry("SELECT * FROM posts;")
    ips = db.querry("SELECT * FROM ips;")

    for user in users:
        text += f"INSERT INTO users(user_name, public_key, key_file, time_created, profile_picture, info) VALUES('{user[0]}', '{user[1]}', '{user[2]}', {user[3]}, '{user[4]}', '{user[5]}');\n"
    
    for post in posts:
        text += f"INSERT INTO posts(id, user_id, post, background_color, time_posted, signature) VALUES('{post[0]}', '{post[1]}', '{post[2]}', '{post[3]}', {post[4]}, '{post[5]}');\n"

    for ip in ips:
        text += f"INSERT INTO ips(ip, time_connected) VALUES('{ip[0]}', {ip[1]});\n"

    text = text.replace("\n", "\u259e").replace("\'", "\u259f")
    connection.send("{"+f'"type":"RESPONSE", "response":"{text}"'+"}")
    
def broadcast(msg, ip):
    global connections, logger

    logger.log(f"bradcasting: {msg} {ip}")

    for connection in connections:
        if not connection.ip == ip:
            msg_text = json.dumps(msg)
            formated_msg = msg_text.replace('"', '\\"')
            connection.queue.append(json.loads("{"+f'"type": "ACTION", "action": "SEND", "msg": "{formated_msg}"'+"}"))

def manage_new_client(connection, conn_info):
    global clients, max_clients, logger
    logger.log(f"managing new client", len(clients))
    conn_class = ClientConnection(connection, conn_info)
    if len(clients) <= max_clients:
        clients.append(conn_class)
        connection.send("OK".encode("utf-8"))
        thread = threading.Thread(target=conn_class.manage_requests)
        thread.start()

# Node - Node comunication
def broadcast_ip(ip:str, node_ip:str):
    global connections
    msg_content = "{"+f'"type": "ACTION", "action": "IP", "ip": "{ip}"'+"}"
    for connection in connections:
        if not connection.ip == node_ip:
            connection.queue.append(json.loads("{"+f'"type": "ACTION", "action": "SEND", "msg": {json.dumps(msg_content)}'+"}"))

def manage_ip(msg_info:dict, node_ip:str):
    global IP, db, clock_time
    ip = msg_info["ip"]
    if ip == IP:
        return

    seconds_to_delete = clock_time * 2
    seconds_to_update = clock_time

    db.execute(f"DELETE FROM ips WHERE time_connected <= {int(time.time()) - seconds_to_delete}")
    res = db.querry(f"SELECT * FROM ips WHERE ip = '{ip}';")

    if len(res) == 0:
        error = db.execute(f"INSERT INTO ips(ip, time_connected) VALUES('{ip}', {time.time()});")
        if not error == "ERROR":
            broadcast_ip(ip, node_ip)

    elif res[0][1] <= int(time.time()) - seconds_to_update:
        err1 = db.execute(f"DELETE FROM ips WHERE ip = '{ip}';")
        err2 = db.execute(f"INSERT INTO ips(ip, time_connected) VALUES('{ip}', {time.time()});")
        if not err1 == "ERROR" and not err2 == "ERROR":
            broadcast_ip(ip, node_ip)


def check_if_connected(ip:str):
    global connections
    for connection in connections:
        if ip == connection.ip:
            return True
    return False

def connect_to_new_node():
    global server_info, db, get_suposed_connected, connections
    n_nodes = len(db.querry("SELECT * FROM ips;"))
    n_suposed_connections = get_suposed_connected(n_nodes)
    n_connected = len(connections)
    if n_suposed_connections < n_connected:
        return
    for i in range(10):
        ip = db.querry("SELECT ip FROM ips ORDER BY RAND() LIMIT 1;")
        if ip and not check_if_connected(ip[0][0]):
            host, port = ip[0][0].split(":")
    
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.connect((host, int(port)))

            connection.send(json.dumps(server_info).encode("utf-8"))

            if connection.recv(1024).decode("utf-8") == "OK":
                #(ip[0][0], connection, ip[0][0])
                conn_class = NodeConnection(connection, {"ip": ip[0][0]}, ip[0][0])
                connections.append(conn_class)
                thread = threading.Thread(target=conn_class.manage_requests)
                thread.start()
                break

        if len(db.querry("SELECT * FROM ips;")) <= len(connections):
            break

def manage_new_node(connection, address, conn_info):
    global connections, get_suposed_connected
    n_connected = len(connections)
    n_nodes = len("SELECT * FROM ips;")
    n_suposed_connections = get_suposed_connected(n_nodes)

    if n_connected < n_suposed_connections and not check_if_connected(conn_info["ip"]):
        connection.send("OK".encode("utf-8"))
        conn_class = NodeConnection(connection, conn_info, address[0]+":"+str(address[1]))
        connections.append(conn_class)
        thread = threading.Thread(target=conn_class.manage_requests)
        thread.start()

def clock():
    global connections, clients, db, IP, logger, clock_time
    while True:
        logger.log("num of connected clients: " + str(len(clients)))
        logger.log("num of connections: " + str(len(connections)))
        for connection in connections:
            logger.log(f"    {connection.ip}")
        res = db.querry("SELECT * FROM ips;")
        logger.log("num of known nodes:" + str(len(res)))
        for ip in res:
            logger.log(f"    {ip[0]}")
        broadcast_ip(IP, IP)
        recomendation.calc_clusters(db)
        time.sleep(clock_time)

def main():
    global server, logger
    while True:
        connection, address = server.accept()
        temp = connection.recv(1024).decode("utf-8")
        logger.log(temp)
        conn_info = json.loads(temp)
        logger.log(conn_info)

        if conn_info["type"] == "NODE":
            manage_new_node(connection, address, conn_info)

        elif conn_info["type"] == "CLIENT":
            manage_new_client(connection, conn_info)

def start():
    global get_suposed_connected, db, connections
    time.sleep(10)
    for i in range(get_suposed_connected(len(db.querry("SELECT * fROM ips;")))):
        connect_to_new_node()
        if len(connections) == 1:
            connections[0].queue.append(json.loads('{"action": "IMPORT"}'))

def init(get_logger:log.Logger, get_clients:list, get_connections:list, get_db:database.Database, get_HOST:str, get_IP:str, get_PORT:str, get_server:socket.socket):
    # sets global variables
    global logger, clients, connections, db, HOST, IP, PORT, get_suposed_connected, server_info, max_clients, server

    logger = get_logger
    clients = get_clients
    connections = get_connections
    db = get_db
    HOST = get_HOST
    IP = get_IP
    PORT = get_PORT
    server = get_server

    get_suposed_connected = lambda n: int(5*math.log2(n))
    get_suposed_connected = lambda n: 3

    server_info = json.loads("{"+f'"type": "NODE", "host": "{HOST}", "port": {PORT}, "ip": "{IP}"'+"}")

    max_clients = 10


logger = log.Logger(None, real=False)
clients = []
connections = []
db = database.Database(real=False)
HOST = ""
IP = ""
PORT = ""

get_suposed_connected = lambda n: 3
server_info = {}
max_clients = math.inf
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clock_time = 86400