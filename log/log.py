import logging
import os

from pythonjsonlogger import jsonlogger


class StackdriverJsonFormatter(jsonlogger.JsonFormatter):
    """
    Stackdriver-specific JSONLogger that ensures proper level names and formatting gets passed to Stackdriver
    """

    def __init__(self, fmt="%(levelname) %(message)", style='%', *args, **kwargs):
        jsonlogger.JsonFormatter.__init__(self, fmt=fmt, *args, **kwargs)

    def process_log_record(self, log_record):
        log_record['severity'] = log_record['levelname']
        del log_record['levelname']
        return super(StackdriverJsonFormatter, self).process_log_record(log_record)


def setup_logger():
    """
    Sets up the required formatters and handlers for the Stackdriver JSON logger.
    Pulls level info from environment if possible
    """
    handler = logging.StreamHandler()
    formatter = StackdriverJsonFormatter()
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level=os.environ.get("LOG_LEVEL", "INFO"))

    gunicorn_logger = logging.getLogger('gunicorn')
    if gunicorn_logger:
        gunicorn_logger.addHandler(handler)
        gunicorn_logger.setLevel(level=os.environ.get("LOG_LEVEL", "INFO"))


def get_logger():
    """Returns the one-and-only logger used by this service"""
    return logging.getLogger()


