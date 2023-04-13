import mysql.connector
import random

class Database:
    def __init__(self):
        pass

    def get_random_ips(self, num:int) -> list[str]:
        ips = [f"127.0.0.1:{port}" for port in range(30001, 30005)]
        return list(set(random.choices(ips, k=num)))