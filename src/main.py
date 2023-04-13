import asyncio
import conn

async def main():
    loop = asyncio.get_running_loop()

    server = await loop.create_server(conn.Connection, "127.0.0.1", 30003)

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())