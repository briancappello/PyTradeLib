import os

# the commission cost per trade
COMMISSION = 10

# the default maximum dollar amount to allocate for a trade
MAX_AMOUNT = 5000

# the number of steps for scaling out of a position
SCALE_OUT_LEVELS = 2 # sell half of quantity half way to the target price and the other half at the target price


###################################################################
DATA_DIR = os.path.join(os.environ['HOME'], '.pytradelib')
ZIPLINE_DIR = os.path.join(os.environ['HOME'], '.zipline')
ZIPLINE_CACHE_DIR = os.path.join(ZIPLINE_DIR, 'cache')

LOG_DIR = os.path.join(DATA_DIR, 'logs')
LOG_FILENAME = os.path.join(LOG_DIR, 'pytradelib.log')
LOG_LEVEL = 'info' # debug, info, warning, error or critical


if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)
