from pytradelib.data import get_symbols_quandl
from pytradelib.utils import exists

# print get_symbols_quandl(['amd', 'f'])

print exists('amd', 'daily')
