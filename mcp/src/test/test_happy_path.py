import logging
from base_test_case import BaseTestCase


class TestHapyPath(BaseTestCase):

    def test_happy_path(self):
        logging.info('Testing Happy Path')
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
