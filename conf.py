import json
import os

def read_config_from_file():
    with open("conf.json", "r") as f:
        str_conf = f.read()
        if str_conf == "" or str_conf == "{}":
            raise EmptyConf()
        conf = json.loads(str_conf)
    return conf

def read_config_from_env():
    try:
        conf = {
            "database": {
                "host": os.environ["MYSQL_HOST"],
                "user": os.environ["MYSQL_USER"],
                "password": os.environ["MYSQL_PASSWORD"],
                "database": os.environ["MYSQL_DATABASE"],
                "root": "root",
                "root_pwd": os.environ["MYSQL_ROOT_PASSWORD"]
            }
        }
    except KeyError:
        raise EmptyConf
    return conf

def init():
    global conf
    conf = read_config_from_env()
    #conf = read_config_from_file()

def api(parameter):
    global conf
    return conf["api"][parameter]

def database(parameter):
    global conf
    print(conf, conf["database"])
    return conf["database"][parameter]

class EmptyConf(Exception):
    def __init__(self):
        super().__init__("Configuration file is empty")

conf = ""
