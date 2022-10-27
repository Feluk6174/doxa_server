from Crypto.PublicKey import RSA
from typing import Union

import auth
import database
import log
import managment
import time
from conn import NodeConnection, ClientConnection

def new_post(msg_info:dict, connection:Union[ClientConnection, NodeConnection], ip:str=None):
    global db, logger
    logger.log(f"posting: {msg_info} {ip}")
    if not database.is_safe(msg_info["post_id"]):
        connection.send("WRONG CHARS")
        return

    pub_key = db.querry(f"SELECT public_key FROM users WHERE user_name = '{msg_info['user_name']}'")
    pub_key = RSA.import_key(auth.reconstruct_key(pub_key[0][0], key_type="pub"))

    if not auth.verify(pub_key, msg_info["signature"], msg_info["content"], msg_info["post_id"], msg_info["user_name"], msg_info["flags"], msg_info["time"]):
        connection.send("WRONG SIGNATURE")
        return
    
    #CREATE TABLE posts(id INT NOT NULL PRIMARY KEY, user_id VARCHAR(16) NOT NULL, post VARCHAR(255) NOT NULL, time_posted INT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_name));")
    res = db.querry(f"SELECT * FROM posts WHERE id = '{msg_info['post_id']}';")
    if len(res) == 0:
        sql = f"INSERT INTO posts(id, user_id, post, flags, time_posted, signature) VALUES('{msg_info['post_id']}', '{msg_info['user_name']}', '{msg_info['content']}', '{msg_info['flags']}', {int(msg_info['time'])}, '{msg_info['signature']}');"
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
    if not database.is_safe(msg_info["user_name"], msg_info['public_key'], msg_info['public_key'], msg_info['profile_picture'], msg_info['info']):
        connection.send("WRONG CHARS")
        return

    #"CREATE TABLE users(user_name VARCHAR(16) NOT NULL UNIQUE PRIMARY KEY, public_key INT NOT NULL UNIQUE, time_created INT NOT NULL, profile_picture VARCHAR(64) NOT NULL, info VARCHAR(255));")
    res = db.querry(f"SELECT * FROM users WHERE user_name = '{msg_info['user_name']}'")

    logger.log("res", res, len(res))
    if len(res) == 0:
        sql = f"INSERT INTO users(user_name, public_key, key_file, time_created, profile_picture, info) VALUES('{msg_info['user_name']}', '{msg_info['public_key']}', '{msg_info['private_key']}', {int(time.time())}, '{msg_info['profile_picture']}', '{msg_info['info']}');"
        logger.log("r"+sql)
        err = db.execute(sql)
        if not err == "ERROR":
            managment.broadcast(msg_info, ip)
            if ip == None:
                connection.send("OK")
        else:
            connection.send("DATABASE ERROR")
    elif ip == None:
        connection.send("ALREADY EXISTS")

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
        msg = "{"+f'"id": "{post[0]}", "user_id": "{post[1]}", "content": "{post[2]}", "flags": "{post[3]}", "time_posted": {post[4]}, "signature": "{post[5]}"'+"}"
        connection.send(msg)
        res = connection.recv_from_queue()
        if not res == "OK":
            logger.log(res)

    connection.send("OK")

def get_posts(msg_info:dict, connection:ClientConnection):
    global db, logger
    logger.log(f"geting posts: {msg_info}")
    logger.log("debug 0")
    #"user_name", "hashtag", "include_flags", "exclude_flags", "sort_by"
    if not database.is_safe(msg_info['user_name'], msg_info["hashtag"], msg_info["include_flags"], msg_info["exclude_flags"], msg_info["sort_by"], msg_info["num"]):
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
        msg_info["user_name"] = msg_info["user_name"].split(",")
        for user_name in msg_info["user_name"]:
            if first:
                first = False
                sql += " WHERE"
            else:
                sql += " AND"

            sql += f" user_id = '{user_name}'"
                

    if not msg_info["hashtag"] == "None":
        if first:
            first = False
            sql += " WHERE"
        else:
            sql += " AND"

        sql += f" INSTR(post, '{msg_info['hashtag']}')"

    if not msg_info["include_flags"] == "None":
        logger.log("kek", type(msg_info["include_flags"]), msg_info["include_flags"])
        for i in range(len(msg_info["include_flags"])):
            if msg_info["include_flags"][i] == "1":
                if first:
                    first = False
                    sql += " WHERE"
                else:
                    sql += " AND"
                
                sql += f" SUBSTR(flags, {i+1}, 1) = '1'"

    if not msg_info["exclude_flags"] == "None":
        for i in range(len(msg_info["exclude_flags"])):
            if msg_info["exclude_flags"][i] == "1":
                if first:
                    first = False
                    sql += " WHERE"
                else:
                    sql += " AND"
                
                sql += f" SUBSTR(flags, {i+1}, 1) = '0'"

    if not msg_info["sort_by"] == "None":
        sql += f" ORDER BY {msg_info['sort_by']}"

    if not msg_info["sort_order"] == "None":
        if msg_info["sort_order"] == "asc" or msg_info["sort_order"] == 0:
            sql += " ASC"
        elif msg_info["sort_order"] == "desc" or msg_info["sort_order"] == 1:
            sql += " DESC"

    if not msg_info["num"] == "None":
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
        msg = "{"+f'"id": "{post[0]}", "user_id": "{post[1]}", "content": "{post[2]}", "flags": "{post[3]}", "time_posted": {post[4]}, "signature": "{post[5]}"'+"}"
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
        msg = "{"+f'"user_name": "{user_info[0]}", "public_key": "{user_info[1]}", "private_key": "{user_info[2]}",  "time_created": {user_info[3]}, "profile_picture": "{user_info[4]}", "info": "{user_info[5]}"'+"}"
    else:
        msg = "{}"
    connection.send(msg)

def get_post(msg_info:dict, connection:ClientConnection):
    global db, logger
    if not database.is_safe(msg_info["post_id"]):
        connection.send("WRONG CHARS")
        return
    # (id, user_id, post, flags, time_posted, signature)
    post = db.querry(f"SELECT * FROM posts WHERE id = '{msg_info['post_id']}';")
    logger.log(post)
    if not len(post) == 0:
        post = post[0]
        msg = "{"+f'"id": "{post[0]}", "user_id": "{post[1]}", "content": "{post[2]}", "flags": "{post[3]}", "time_posted": {post[4]}, "signature": "{post[5]}"'+"}"
    else:
        msg = "{}"
    connection.send(msg)

def init(get_logger:log.Logger, get_db:database.Database):
    # sets global variables
    global logger, db

    logger.stop()
    logger = get_logger
    db.stop()
    db = get_db

logger = log.Logger(None)
db = database.Database()

from conn import NodeConnection, ClientConnection
