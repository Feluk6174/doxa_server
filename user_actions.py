from Crypto.PublicKey import RSA
from typing import Union
import random
import json

import auth
import database
import log
import managment
import time
import recomendation
from conn import NodeConnection, ClientConnection

def new_post(msg_info:dict, connection:Union[ClientConnection, NodeConnection], ip:str=None):
    global db, logger
    logger.log(f"posting: {msg_info} {ip}")
    if not database.is_safe(msg_info["post_id"]):
        connection.send("WRONG CHARS")
        logger.log("WRONG CHARS")
        return

    pub_key = db.querry(f"SELECT public_key FROM users WHERE user_name = '{msg_info['user_name']}'")
    pub_key = RSA.import_key(auth.reconstruct_key(pub_key[0][0], key_type="pub"))

    if not auth.verify(pub_key, msg_info["signature"], msg_info["content"], msg_info["post_id"], msg_info["user_name"], msg_info["background_color"], msg_info["time"]):
        connection.send("WRONG SIGNATURE")
        logger.log("WRONG SIGNATURE")
        return
    
    #CREATE TABLE posts(id INT NOT NULL PRIMARY KEY, user_id VARCHAR(16) NOT NULL, post VARCHAR(255) NOT NULL, time_posted INT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_name));")
    res = db.querry(f"SELECT * FROM posts WHERE id = '{msg_info['post_id']}';")
    logger.log(res)
    if len(res) == 0:
        sql = f"INSERT INTO posts(id, user_id, post, background_color, time_posted, signature) VALUES('{msg_info['post_id']}', '{msg_info['user_name']}', '{msg_info['content']}', '{msg_info['background_color']}', {int(msg_info['time'])}, '{msg_info['signature']}');"
        err = db.execute(sql)
        if not err == "ERROR":
            managment.broadcast(msg_info, ip)
            if ip == None:
                connection.send('OK')
        else:
            connection.send('DATABASE ERROR')
    elif ip == None:
        connection.send("ALREADY EXISTS")


def register_user(msg_info:dict, connection:Union[ClientConnection, NodeConnection], ip:str=None):
    global db, logger
    logger.log(f"registering user: {msg_info} {ip}")
    if not database.is_safe(msg_info["user_name"], msg_info['public_key'], msg_info['public_key'], msg_info['profile_picture'], msg_info['info'], msg_info["grup"], msg_info["pos"]):
        connection.send("WRONG CHARS")
        logger.log("WRONG CHARS")
        return

    #"CREATE TABLE users(user_name VARCHAR(16) NOT NULL UNIQUE PRIMARY KEY, public_key INT NOT NULL UNIQUE, time_created INT NOT NULL, profile_picture VARCHAR(64) NOT NULL, info VARCHAR(255));")
    res = db.querry(f"SELECT * FROM users WHERE user_name = '{msg_info['user_name']}'")
    logger.log(res)

    logger.log("res", res, len(res))
    if len(res) == 0:
        sql = f"INSERT INTO users(user_name, public_key, key_file, time_created, profile_picture, info, grup, pos) VALUES('{msg_info['user_name']}', '{msg_info['public_key']}', '{msg_info['private_key']}', {int(time.time())}, '{msg_info['profile_picture']}', '{msg_info['info']}', {msg_info['grup']}, '{json.dumps(msg_info['pos'])}');"
        logger.log("r"+sql)
        err = db.execute(sql)
        if not err == "ERROR":
            managment.broadcast(msg_info, ip)
            if ip == None:
                connection.send("OK")
        else:
            connection.send("DATABASE ERROR")
            logger.log("DATABASE ERROR")
    elif ip == None:
        connection.send("ALREADY EXISTS")
        logger.log("ALREADY EXISTS")

def change_profile_picture(msg_info:dict, connection:Union[ClientConnection, NodeConnection], ip:str=None):
    global db, logger
    logger.log(f"changing pp: {msg_info} {ip}")
    if not database.is_safe(msg_info["profile_picture"], msg_info["user_name"]):
        connection.send("WRONG CHARS")
        return

    pub_key = db.querry(f"SELECT public_key FROM users WHERE user_name = '{msg_info['user_name']}'")
    pub_key = RSA.import_key(auth.reconstruct_key(pub_key[0][0], key_type="pub"))

    if not auth.verify(pub_key, msg_info["signature"], msg_info["user_name"], msg_info["profile_picture"], msg_info["time"]):
        connection.send("WRONG SIGNATURE")
        return
    
    res = db.querry(f"SELECT * FROM users WHERE user_name = '{msg_info['user_name']}' AND profile_picture = '{msg_info['profile_picture']}';")
    if len(res) == 0:
        sql = f"UPDATE users SET profile_picture = '{msg_info['profile_picture']}' WHERE user_name = '{msg_info['user_name']}';"
        err = db.execute(sql)
        if not err == "ERROR":
            managment.broadcast(msg_info, ip)
            if ip == None:
                connection.send('OK')
        elif ip == None:
            connection.send('DATABASE ERROR')
    elif ip == None:
        connection.send("OK")

def change_info(msg_info:dict, connection:Union[ClientConnection, NodeConnection], ip:str=None):
    global db, logger
    logger.log(f"changing info: {msg_info} {ip}")
    if not database.is_safe(msg_info["info"], msg_info["user_name"]):
        connection.send("WRONG CHARS")
        return

    pub_key = db.querry(f"SELECT public_key FROM users WHERE user_name = '{msg_info['user_name']}'")
    pub_key = RSA.import_key(auth.reconstruct_key(pub_key[0][0], key_type="pub"))

    if not auth.verify(pub_key, msg_info["signature"], msg_info["user_name"], msg_info["info"], msg_info["time"]):
        connection.send("WRONG SIGNATURE")
        return
    
    res = db.querry(f"SELECT * FROM users WHERE user_name = '{msg_info['user_name']}' AND info = '{msg_info['info']}';")
    if len(res) == 0:
        sql = f"UPDATE users SET info = '{msg_info['info']}' WHERE user_name = '{msg_info['user_name']}';"
        err = db.execute(sql)
        if not err == "ERROR":
            managment.broadcast(msg_info, ip)
            if ip == None:
                connection.send('OK')
        elif ip == None:
            connection.send('DATABASE ERROR')
    elif ip == None:
        connection.send("OK")


def update_pos(msg_info:dict, connection:Union[ClientConnection, NodeConnection], ip:str=None):
    global db, logger
    logger.log(f"changing info: {msg_info} {ip}")
    if not database.is_safe(msg_info["pos"], msg_info["user_name"], logger=logger):
        connection.send("WRONG CHARS")
        return

    pub_key = db.querry(f"SELECT public_key FROM users WHERE user_name = '{msg_info['user_name']}'")
    pub_key = RSA.import_key(auth.reconstruct_key(pub_key[0][0], key_type="pub"))

    if not auth.verify(pub_key, msg_info["signature"], msg_info["user_name"], msg_info["pos"], msg_info["time"]):
        connection.send("WRONG SIGNATURE")
        return
    
    res = db.querry(f"SELECT * FROM users WHERE user_name = '{msg_info['user_name']}' AND pos = '{msg_info['pos']}';")
    if len(res) == 0:
        sql = f"UPDATE users SET pos = '{msg_info['pos']}' WHERE user_name = '{msg_info['user_name']}';"
        err = db.execute(sql)
        if not err == "ERROR":
            managment.broadcast(msg_info, ip)
            if ip == None:
                connection.send('OK')
        elif ip == None:
            connection.send('DATABASE ERROR')
    elif ip == None:
        connection.send("OK")

def get_user_posts(msg_info:dict, connection:ClientConnection):
    global db, logger
    logger.log(f"geting posts: {msg_info}")

    if not database.is_safe(msg_info['user_name']):
        connection.send("0")
        res = connection.recv_from_queue()
        if not res == "OK":
            logger.log(res)
        connection.send("WRONG CHARS")
        return

    posts = db.querry(f"SELECT * FROM posts WHERE user_id = '{msg_info['user_name']}'")

    connection.send(str(len(posts)))

    res = connection.recv_from_queue()
    logger.log("res1", res)
    if not res == "OK":
        logger.log(res)

    for i, post in enumerate(posts):
        msg = "{"+f'"id": "{post[0]}", "user_id": "{post[1]}", "content": "{post[2]}", "background_color": "{post[3]}", "time_posted": {post[4]}, "signature": "{post[5]}"'+"}"
        connection.send(msg)
        res = connection.recv_from_queue()
        if not res == "OK":
            logger.log(res)

    connection.send("OK")

def get_posts(msg_info:dict, connection:ClientConnection):
    global db, logger
    logger.log(f"geting posts: {msg_info}")
    logger.log("debug 0")
    #"user_name", "hashtag", "include_background_color", "exclude_background_color", "sort_by"
    if not database.is_safe(msg_info['user_name'], msg_info["hashtag"], msg_info["include_background_color"], msg_info["exclude_background_color"], msg_info["sort_by"], msg_info["num"], msg_info["id"]):
        connection.send("0")
        res = connection.recv_from_queue()
        if not res == "OK":
            logger.log(res)
        connection.send("WRONG CHARS")
        return
    logger.log("debug 1")
    first = True

    sql = "SELECT * FROM posts"

    if not msg_info["user_name"] == "None":
        if first:
            first = False
            sql += " WHERE ("
        else:
            sql += " AND ("

        msg_info["user_name"] = msg_info["user_name"].split(",")
        logger.log(msg_info["user_name"])
        for i, user_name in enumerate(msg_info["user_name"]):
            sql += f" user_id = '{user_name}'"
            #logger.log(i, len(msg_info)-1, i == len(msg_info)-1)
            if not i == len(msg_info["user_name"])-1:
                sql += " OR"
            else:
                sql += ")"

    if not msg_info["id"] == "None":
        if first:
            first = False
            sql += " WHERE ("
        else:
            sql += " AND ("

        msg_info["id"] = msg_info["id"].split(",")
        logger.log(msg_info["id"])
        for i, id in enumerate(msg_info["id"]):
            sql += f" id = '{id}'"
            #logger.log(i, len(msg_info)-1, i == len(msg_info)-1)
            if not i == len(msg_info["id"])-1:
                sql += " OR"
            else:
                sql += ")"


    if not msg_info["hashtag"] == "None":
        if first:
            first = False
            sql += " WHERE"
        else:
            sql += " AND"

        sql += f" INSTR(post, '{msg_info['hashtag']}')"

    if not msg_info["include_background_color"] == "None":
        logger.log("kek", type(msg_info["include_background_color"]), msg_info["include_background_color"])
        for i in range(len(msg_info["include_background_color"])):
            if msg_info["include_background_color"][i] == "1":
                if first:
                    first = False
                    sql += " WHERE"
                else:
                    sql += " AND"
                
                sql += f" background_color = '{msg_info['include_background_color']}'"

    if not msg_info["exclude_background_color"] == "None":
        for i in range(len(msg_info["exclude_background_color"])):
            if msg_info["exclude_background_color"][i] == "1":
                if first:
                    first = False
                    sql += " WHERE"
                else:
                    sql += " AND"
                
                sql += f" not background_color = '{msg_info['include_background_color']}'"

    if not msg_info["grup"] == "None":
        if first:
            first = False
            sql += " WHERE"
        else:
            sql += " AND"

        sql += f" user_id IN (SELECT user_name FROM users WHERE grup = {msg_info['grup']})"

    if not msg_info["sort_by"] == "None":
        sql += f" ORDER BY {msg_info['sort_by']}"

    if not msg_info["sort_order"] == "None":
        if msg_info["sort_order"] == "asc" or msg_info["sort_order"] == 0:
            sql += " ASC"
        elif msg_info["sort_order"] == "desc" or msg_info["sort_order"] == 1:
            sql += " DESC"

    

    try:
        sql += f" LIMIT {msg_info['offset']}, {msg_info['num']}"
    except KeyError:
        sql += f" LIMIT {msg_info['num']}"

    sql += ";"

    logger.log("sql", sql)

    posts = db.querry(sql)

    connection.send(str(len(posts)))

    res = connection.recv_from_queue()
    logger.log("res1", res)
    if not res == "OK":
        logger.log(res)

    logger.log("www", posts)

    for i, post in enumerate(posts):
        msg = "{"+f'"id": "{post[0]}", "user_id": "{post[1]}", "content": "{post[2]}", "background_color": "{post[3]}", "time_posted": {post[4]}, "signature": "{post[5]}"'+"}"
        connection.send(msg)
        res = connection.recv_from_queue()
        if not res == "OK":
            logger.log(res)

    connection.send("OK")

def get_user_info(msg_info:dict, connection:ClientConnection):
    global db, logger
    if not database.is_safe(msg_info["user_name"]):
        connection.send("WRONG CHARS")
        return
    # (user_name, public_key, key_file, time_created, profile_picture, info)
    user_info = db.querry(f"SELECT * FROM users WHERE user_name = '{msg_info['user_name']}';")
    logger.log(user_info)
    if not len(user_info) == 0 and not user_info == "ERROR":
        user_info = user_info[0]
        msg = "{"+f'"user_name": "{user_info[0]}", "public_key": "{user_info[1]}", "private_key": "{user_info[2]}",  "time_created": {user_info[3]}, "profile_picture": "{user_info[4]}", "info": "{user_info[5]}", "grup": {user_info[6]}, "pos": '+"{}}"
        msg = json.loads(msg)
        msg["pos"] = json.loads(user_info[7])
        msg = json.dumps(msg)
    else:
        msg = "{}"
    connection.send(msg)


def get_users_info(msg_info:dict, connection:ClientConnection):
    global db, logger
    if not database.is_safe(msg_info["user_names"]):
        connection.send("WRONG CHARS")
        return
    # (user_name, public_key, key_file, time_created, profile_picture, info)
    sql = "SELECT * FROM users "
    first = True
    for user in msg_info["user_names"].split(","):
        if first:
            first = False
            sql += " WHERE"
        else:
            sql += " OR"
        sql += f" user_name = '{user}'"

    sql += ";"
    users = db.querry(sql)

    connection.send(str(len(users)))

    res = connection.recv_from_queue()
    logger.log("res1", res)
    if not res == "OK":
        logger.log(res)

    for i, user_info in enumerate(users):
        logger.log(users)
        msg = "{"+f'"user_name": "{user_info[0]}", "public_key": "{user_info[1]}", "private_key": "{user_info[2]}",  "time_created": {user_info[3]}, "profile_picture": "{user_info[4]}", "info": "{user_info[5]}", "grup": {user_info[6]}, "pos": '+"{}}"
        msg = json.loads(msg)
        msg["pos"] = json.loads(user_info[7])
        msg = json.dumps(msg)
        connection.send(msg)
        res = connection.recv_from_queue()
        if not res == "OK":
            logger.log(res)

def get_post(msg_info:dict, connection:ClientConnection):
    global db, logger
    if not database.is_safe(msg_info["post_id"]):
        connection.send("WRONG CHARS")
        return
    # (id, user_id, post, background_color, time_posted, signature)
    post = db.querry(f"SELECT * FROM posts WHERE id = '{msg_info['post_id']}';")
    logger.log(post)
    if not len(post) == 0:
        post = post[0]
        msg = "{"+f'"id": "{post[0]}", "user_id": "{post[1]}", "content": "{post[2]}", "background_color": "{post[3]}", "time_posted": {post[4]}, "signature": "{post[5]}"'+"}"
    else:
        msg = "{}"
    connection.send(msg)

def get_ips(msg_info:dict, connection:ClientConnection):
    global logger
    ips = db.querry("SELECT ip FROM ips ORDER BY RAND() LIMIT 10;")
    ips = [ip[0] for ip in ips]
    msg = {"ips": ips}
    logger.log("ips", msg)
    connection.send(json.dumps(msg))

def init(get_logger:log.Logger, get_db:database.Database):
    # sets global variables
    global logger, db

    logger = get_logger
    db = get_db

logger = log.Logger(None, real=False)
db = database.Database(real=False)

from conn import NodeConnection, ClientConnection
