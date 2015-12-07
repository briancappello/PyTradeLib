def get_constants(prefix):
    consts = filter(lambda c: c[0].startswith(prefix), globals().items())
    return map(lambda c: c[1], consts)

ACTION_BUY = 'BUY'
ACTION_SELL = 'SELL'
ACTION_SHORT = 'SHORT'
ACTIONS = get_constants('ACTION_')

TYPE_MARKET = 'MARKET'
TYPE_LIMIT = 'LIMIT'
TYPE_STOP = 'STOP'
TYPE_STOP_LIMIT = 'STOP_LIMIT'
TYPES = get_constants('TYPE_')

TIMING_DAY = 'DAY_ONLY'
TIMING_GOOD_TILL_CANCELED = 'GOOD_TILL_CANCELED'
TIMING_FILL_OR_KILL = 'FILL_OR_KILL'
TIMING_IMMEDIATE_OR_CANCEL = 'IMMEDIATE_OR_CANCEL'
TIMINGS = get_constants('TIMING_')


class Order(object):
    def __init__(self, action, quantity, ticker, type, price):
        self.action = action
        self.quantity = quantity
        self.ticker = ticker
        self.type = type
        self.price = price

    @property
    def action(self):
        return self.__action

    @action.setter
    def action(self, action):
        if action not in ACTIONS:
            raise Exception('param action must be one of %s' % ', '.join(ACTIONS))
        self.__action = action

    @property
    def quantity(self):
        return self.__quantity

    @quantity.setter
    def quantity(self, quantity):
        if not int(quantity):
            raise Exception('param quantity must be greater than 0')
        self.__quantity = int(quantity)

    @property
    def ticker(self):
        return self.__ticker

    @ticker.setter
    def ticker(self, ticker):
        self.__ticker = ticker.upper()

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, type):
        if type not in TYPES:
            raise Exception('param type must be one of %s' % ', '.join(TYPES))
        self.__type = type

    @property
    def price(self):
        return self.__price

    @price.setter
    def price(self, price):
        try:
            self.__price = float(price)
        except TypeError:
            self.__price = None
        if not self.__price or self.__price <= 0:
            raise Exception('param price must be greater than 0')
