import unittest
import logging
import asyncio


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Reset logging disable level to ensure logs are not suppressed
        logging.disable(logging.NOTSET)
        # Configure basic logging to console at DEBUG level
        logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        # Set the logging level to WARNING to ignore INFO and DEBUG logs
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)


class BaseAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Reset logging disable level to ensure logs are not suppressed
        logging.disable(logging.NOTSET)
        # Configure basic logging to console at DEBUG level
        logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)


if __name__ == '__main__':
    pass
