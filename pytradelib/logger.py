import logging
from logging.handlers import TimedRotatingFileHandler

from pytradelib.settings import LOG_LEVEL, LOG_FILENAME

LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

logger = logging.getLogger('PyTradeLib')
logger.setLevel(LEVELS.get(LOG_LEVEL, logging.WARNING))
handler = TimedRotatingFileHandler(LOG_FILENAME, 'midnight')
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: pytradelib.%(module)s L%(lineno)s: %(message)s',
    '%Y-%m-%d %H:%M:%S'
))
logger.addHandler(handler)


__ALL__ = ('logger',)
