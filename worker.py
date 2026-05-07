import asyncio
import logging

logger = logging.getLogger(__name__)


async def run_background_tasks() -> None:
    logger.info("Background worker started")
    while True:
        try:
            # Add background tasks here as needed
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_background_tasks())
