import mysql.connector
import random
import threading
import time
import log as log_lib
import conf
import json

#TODO:
#Executemany

def log(*message, logger:log_lib.Logger = None):
    if not logger == None:
        logger.log(*message)
    else:
        print(message)

def is_safe(*args, logger = None):
    invalid_chars = ["\\", "\n", "\t", "\r", "\0", "%", "\b", ";", "\u259e"]

    arguments = ""
    for argument in args:
        arguments += str(argument) if not argument == None else ""


    log("arguments", arguments, logger=logger)
    for i, char in enumerate(invalid_chars):
        if char in arguments:
            log(f"[ERROR] Invalid char {char} [{i}]", logger=logger)
            return False
    return True


class Database():
    def __init__(self, logger:log_lib.Logger=None, real=True):
        if not real:
            return
        time.sleep(5)
        self.connect()
        self.queue = []
        self.return_response = []
        self.logger = logger
        self.file = open("sql.txt", "a")
        thread = threading.Thread(target=self.proces_queue)
        thread.start()

    def connect(self):
        conf.init()
        self.connection = mysql.connector.connect(
            host = conf.database("host"), 
            user = conf.database("root"), 
            password = conf.database("root_pwd"),
            database = conf.database("database")
        )

    def stop(self):
        queue_id = random.randint(1000000000, 9999999999)
        self.queue.append(("s", "stop", queue_id))

    def get_users_with_pos(self):
        users = self.querry("SELECT user_name, grup, pos FROM users;")
        users = [[user[0], user[1], json.loads(user[2])["pos"]] for user in users]
        return users

    def update_users_pos(self, users:list[list]):
        for user in users:
            self.execute(f"UPDATE users SET grup = {user[1]} WHERE user_name = '{user[0]}';")

    def querry(self, querry:str):
        queue_id = random.randint(1000000000, 9999999999)
        self.queue.append(("q", querry, queue_id))
        while True:
            for response in self.return_response:
                if response[0] == queue_id:
                    self.return_response.remove((queue_id, response[1]))
                    return response[1]


    def execute(self, sql:str):
        queue_id = random.randint(1000000000, 9999999999)
        self.queue.append(("e", sql, queue_id))
        while True:
            for response in self.return_response:
                if response[0] == queue_id:
                    self.return_response.remove((queue_id, response[1]))
                    return response[1]

    def import_db(self, commands:list):
        queue_id = random.randint(1000000000, 9999999999)
        self.queue.append(("n", commands, queue_id))
        while True:
            for response in self.return_response:
                if response[0] == queue_id:
                    self.return_response.remove((queue_id, response[1]))
                    return response[1]

    def proces_queue(self):
        log("[STARTED QUEUE PROCESOR]", logger=self.logger)
        while True:
            if len(self.queue) > 0:
                if self.queue[0][0] == "q":
                    try:
                        cursor = self.connection.cursor()
                        cursor.execute(self.queue[0][1])
                        self.return_response.append((self.queue[0][2], cursor.fetchall()))

                    except mysql.connector.Error as e:
                        self.connect()
                        try:
                            cursor = self.connection.cursor()
                            cursor.execute(self.queue[0][1])
                            self.return_response.append((self.queue[0][2], cursor.fetchall()))
                            
                        except mysql.connector.Error as e:
                            log("[ERROR]", e, logger = self.logger)
                            self.connect()
                            self.return_response.append((self.queue[0][2], "ERROR"))

                elif self.queue[0][0] == "e":
                    try:
                        cursor = self.connection.cursor()
                        cursor.execute(self.queue[0][1])
                        self.connection.commit()
                        self.return_response.append((self.queue[0][2], None))
                        self.file.write(self.queue[0][1]+"\n")
                        
                    except mysql.connector.Error as e:
                        self.connect()
                        try:
                            cursor = self.connection.cursor()
                            cursor.execute(self.queue[0][1])
                            self.connection.commit()
                            self.return_response.append((self.queue[0][2], None))
                            self.file.write(self.queue[0][1]+"\n")
                        except mysql.connector.Error as e:
                            log("[ERROR]", e, logger = self.logger)
                            self.connect()
                            self.return_response.append((self.queue[0][2], "ERROR"))
                
                elif self.queue[0][0] == "n":
                    try:
                        cursor = self.connection.cursor()
                        for command in self.queue[0][1]: 
                            try: 
                                cursor.execute(command)
                            except mysql.connector.Error as e:
                                pass
                        self.connection.commit()
                        self.return_response.append((self.queue[0][2], "SUCCESS"))
                    except mysql.connector.Error as e:
                        try:
                            self.connect()
                            cursor = self.connection.cursor()
                            for command in self.queue[0][1]: 
                                try: 
                                    cursor.execute(command)
                                except mysql.connector.Error as e:
                                    pass
                            self.connection.commit()
                            self.return_response.append((self.queue[0][2], "SUCCESS"))
                        except mysql.connector.Error as e:
                            log("[ERROR]", e, logger = self.logger)
                            self.connect()
                            self.return_response.append((self.queue[0][2], "ERROR"))
                        


                elif self.queue[0][0] == "s":
                    self.queue.pop(0)
                    break

                self.queue.pop(0)
            time.sleep(0.1)

    def drop(self):
        cursor = self.connection.cursor()

        cursor.execute("DROP TABLE IF EXISTS posts;")
        cursor.execute("DROP TABLE IF EXISTS users;")
        cursor.execute("DROP TABLE IF EXISTS grups;")
        cursor.execute("DROP TABLE IF EXISTS ips;")

    def create(self):
        cursor = self.connection.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS grups(id INT NOT NULL PRIMARY KEY, pos JSON NOT NULL);")
        cursor.execute("CREATE TABLE IF NOT EXISTS users(user_name VARCHAR(16) COLLATE ascii_general_ci NOT NULL UNIQUE PRIMARY KEY, public_key VARCHAR(392) COLLATE ascii_general_ci NOT NULL UNIQUE, key_file VARCHAR(1764) COLLATE ascii_general_ci NOT NULL UNIQUE, time_created INT NOT NULL, profile_picture VARCHAR(64) COLLATE ascii_general_ci NOT NULL, info VARCHAR(200), grup INT NOT NULL, pos JSON, FOREIGN KEY (grup) REFERENCES grups (id) ON UPDATE CASCADE);")
        cursor.execute("CREATE TABLE IF NOT EXISTS posts(id VARCHAR(23) NOT NULL PRIMARY KEY, user_id VARCHAR(16) COLLATE ascii_general_ci NOT NULL, post VARCHAR(255) NOT NULL, background_color VARCHAR(1) NOT NULL, time_posted INT NOT NULL, signature VARCHAR(344), FOREIGN KEY (user_id) REFERENCES users (user_name));")
    
        cursor.execute("CREATE TABLE IF NOT EXISTS ips(ip VARCHAR(21) NOT NULL PRIMARY KEY, time_connected INT NOT NULL);")

        self.connection.commit()

"""if __name__ == "__main__":
    db = Database()
    db.create()
    db.stop()"""
