import asyncio
import json
import management
import user_actions

class Connection(asyncio.Protocol):
    new:bool = True
    read:int = 0
    size:int = 0

    def __init__(self) -> None:
        global connections
        print(1)
        connections.append(self)

    def connection_made(self, transport: asyncio.transports.Transport) -> None:
        self.info:tuple[str, int] = transport.get_extra_info('peername')
        self.transport = transport
        print(f"connected by {self.info}")

    def connection_lost(self, exc: Exception | None) -> None:
        global connections
        print(f"disconnected from {self.info}")
        connections.remove(self)

    def data_received(self, data: bytes) -> None:
        """This function gets the data that is recieved throug TCP

        Args:
            data (bytes): The data recieved over TCP
        """

        # Splits and unifies the data recieved to the intended message
        message:bytearray = bytearray()
        for byte in data:
            # The first 8 bytes of a message indicate the size of it
            # This calculates the size of the message
            if self.read < 8:
                self.size += int(byte)*(10**(8-self.read))
            else:
                message.append(byte)
            
            if self.read == self.size+7 and not self.read == 0:
                self.read = 0
                self.size = 0
            else:
                self.read += 1

        message_str:dict = json.loads(message.decode("utf-8"))
        self.manage_message(message_str)

    def broadcast(self, data:bytes) -> None:
        global connections
        for connection in connections:
            if not connection == self:
                connection.transport.write(data)

    def manage_message(self, message:dict) -> None:
        if message["action"] == "IP":
            #TODO
            management.manage_ip(message, self)

        elif message["action"] == "REGISTER":
            #TODO
            user_actions.register(message, self)

        elif message["action"] == "POST":
            #TODO
            user_actions.post(message, self)

        elif message["action"] == "UPDATE PROFILE PICTURE":
            #TODO
            user_actions.change_profile_picture(message, self)

        elif message["action"] == "UPDATE INFO":
            #TODO
            user_actions.change_info(message, self)

        elif message["action"] == "UPDATE POS":
            #TODO
            user_actions.update_pos(message, self)

        elif message["action"] == "EXPORT":
            #TODO
            management.export_db(self)

        elif message["action"] == "IMPORT":
            #TODO
            management.import_db(self)

        elif message["action"] == "GET POSTS":
            #TODO
            user_actions.get_posts(message, self)

        elif message["action"] == "GET USER":
            #TODO
            user_actions.get_user_info(message, self)

        elif message["action"] == "GET USERS":
            #TODO
            user_actions.get_users_info(message, self)

        elif message["action"] == "GET POST":
            #TODO
            user_actions.get_post(message, self)
                
        elif message["action"] == "GET IPS":
            #TODO
            user_actions.get_ips(message, self)

        if message["action"] == "SEND":
            #TODO
            self.transport.write(message["msg"])

connections: list[Connection] = []
