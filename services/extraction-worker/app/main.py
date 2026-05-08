import asyncio
import logging

from app.consumer import Consumer


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def main() -> None:
    configure_logging()
    consumer = Consumer()
    await consumer.run()


if __name__ == "__main__":
    asyncio.run(main())
