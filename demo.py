import asyncio
import time

async def hello():
    await asyncio.sleep(1)
    print("hello end")

async def main():
    hello()
    print("main end")


if __name__ == "__main__":
    asyncio.run(main())