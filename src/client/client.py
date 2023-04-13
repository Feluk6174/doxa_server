import asyncio

class ClientProtocol(asyncio.Protocol):
    user_name = ""
    def __init__(self) -> None:
        pass

    def connection_made(self, transport: asyncio.transports.Transport) -> None:
        print("connected", transport.get_protocol())
        self.transport = transport
        self.transport.resume_reading()

    def connection_lost(self, exc: Exception | None) -> None:
        print("disconnected")

    def data_received(self, data: bytes) -> None:
        print(1)
        print(data)
    
    def send(self, data:bytes):
        self.transport.write(data)

    def set_user_name(self, user_name:str) -> None:
        self.user_name = user_name

    

async def main(text):
    #user_name = input("User name: ")
    user_name = text
    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_connection(ClientProtocol, "127.0.0.1", 30003)
    protocol.set_user_name(user_name)
    protocol.send(user_name.encode("utf-8"))

    while True:
        protocol.send(text.encode("utf-8"))
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main(input("text: ")))