from trickster.logger import get_logger


class TestGetLogger:
    def test_get_logger(self):
        logger = get_logger()
        assert logger.name == 'trickster'

    def test_get_logger_is_cached(self):
        assert get_logger() is get_logger()

