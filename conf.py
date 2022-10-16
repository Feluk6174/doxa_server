import json

def init():
    global conf
    with open("conf.json", "r") as f:
        str_conf = f.read()
        if str_conf == "" or str_conf == "{}":
            raise EmptyConf()
        conf = json.loads(str_conf)

def api(parameter):
    global conf
    return conf["api"][parameter]

def database(parameter):
    global conf
    return conf["database"][parameter]

class EmptyConf(Exception):
    def __init__(self):
        super().__init__("Configuration file is empty")

conf = ""
init()