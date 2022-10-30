import mysql.connector
import random
import threading
import time
import log as log_lib
import conf


def log(*message, logger:log_lib.Logger = None):
    if not logger == None:
        logger.log(*message)
    else:
        print(message)

def is_safe(*args, logger = None):
    invalid_chars = ["\\", "\'", "\"", "\n", "\t", "\r", "\0", "%", "\b", ";", "=", "\u259e"]

    arguments = ""
    for argument in args:
        arguments += argument if not argument == None else ""

    for char in invalid_chars:
        if char in arguments:
            log(f"[ERROR] Invalid char {char}", logger)
            return False
    return True


class Database():
    def __init__(self, logger:log_lib.Logger=None):
        self.connect()
        self.queue = []
        self.return_response = []
        self.logger = logger
        self.file = open("sql.txt", "a")
        thread = threading.Thread(target=self.proces_queue)
        thread.start()

    def connect(self):
        self.connection = mysql.connector.connect(
            host = conf.database("host"), 
            user = conf.database("user"), 
            password = conf.database("password"),
            database = conf.database("database")
        )

    def stop(self):
        queue_id = random.randint(1000000000, 9999999999)
        self.queue.append(("s", "stop", queue_id))

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
        self.queue.append("n", commands, queue_id)
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
                        except mysql.connector.Error as e:
                            log("[ERROR]", e, logger = self.logger)
                            self.connect()
                            self.return_response.append((self.queue[0][2], "ERROR"))
                
                elif self.queue[0][0] == "n":
                    try:
                        cursor = self.connection.cursor()
                        for command in self.queue[0][1]:
                            cursor.execute(command)
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


    def create(self):
        cursor = self.connection.cursor()

        cursor.execute("DROP TABLE IF EXISTS posts;")
        cursor.execute("DROP TABLE IF EXISTS users;")

        cursor.execute("CREATE TABLE users(user_name VARCHAR(16) COLLATE ascii_general_ci NOT NULL UNIQUE PRIMARY KEY, public_key VARCHAR(392) COLLATE ascii_general_ci NOT NULL UNIQUE, key_file VARCHAR(1764) COLLATE ascii_general_ci NOT NULL UNIQUE, time_created INT NOT NULL, profile_picture VARCHAR(64) COLLATE ascii_general_ci NOT NULL, info VARCHAR(200));")
        cursor.execute("CREATE TABLE posts(id VARCHAR(23) NOT NULL PRIMARY KEY, user_id VARCHAR(16) COLLATE ascii_general_ci NOT NULL, post VARCHAR(255) NOT NULL, background_color VARCHAR(1) NOT NULL, time_posted INT NOT NULL, signature VARCHAR(344), FOREIGN KEY (user_id) REFERENCES users (user_name));")
    
        cursor.execute("DROP TABLE IF EXISTS ips;")

        cursor.execute("CREATE TABLE ips(ip VARCHAR(21) NOT NULL PRIMARY KEY, time_connected INT NOT NULL);")

        self.connection.commit()

if __name__ == "__main__":
    db = Database()
    db.create()
    db.stop()
