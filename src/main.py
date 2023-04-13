import asyncio

class Server(asyncio.Protocol):
    new = True
    user_name = ""

    def __init__(self) -> None:
        global connections
        print(1)
        connections.append(self)

    def connection_made(self, transport: asyncio.transports.Transport) -> None:
        print("connected", transport.get_protocol())
        self.transport = transport

    def connection_lost(self, exc: Exception | None) -> None:
        global connections
        print("disconnected")
        connections.remove(self)

    def data_received(self, data: bytes) -> None:
        print(self.new, data)
        if self.new:
            self.new = False
            self.user_name = data.decode("utf-8")
            self.transport.write(data)
            self.broadcast(f"{self.user_name} connected".encode("utf-8"))

        else:
            self.transport.write(data)
            self.broadcast(f"{self.user_name}: ".encode("utf-8")+data)

    def broadcast(self, data:bytes) -> None:
        global connections
        for connection in connections:
            connection.transport.write(data)

async def main():
    loop = asyncio.get_running_loop()

    server = await loop.create_server(Server, "127.0.0.1", 30003)

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    connections: list[Server] = []
    asyncio.run(main())