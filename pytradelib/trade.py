from __future__ import print_function

import re
import sys

from colorclass import Color
from terminaltables import AsciiTable

from pytradelib.hash import Hash
from pytradelib.settings import (
    COMMISSION,
    MAX_AMOUNT,
    SCALE_OUT_LEVELS
)
from pytradelib.models.order import (
    Order,
    ACTION_BUY,
    ACTION_SELL,
    ACTION_SHORT,
    TYPE_MARKET,
    TYPE_LIMIT,
    TYPE_STOP,
    TYPE_STOP_LIMIT,
    TIMING_DAY,
    TIMING_GOOD_TILL_CANCELED,
)



class Trade(object):
    entry = None
    exits = []

    def __init__(self, entry, exits):
        pass


def error():
    print('Command should be in the format of:\n <buy|sell> [quantity] <ticker> at <price>, <sell|buy> at <target_price> or <stop_price>')
    sys.exit(1)

'''
action [q] ticker stop 4 limit 5
action [q] ticker at 5  # limit order
'''

REGEXES = {
    'limit': re.compile('''
    ^ # action [quantity] ticker at price
    (?P<action>(buy|sell))            # entry action: buy or sell
    (?:(?P<quantity>\d+))?\s?         # quantity: optional, int
    (?P<ticker>\w+)                   # ticker: string
    \sat\s
    (?P<price>(?:\d+\.)?\d+)          # price: int or float
    $
    ''', re.VERBOSE),

    'stop_limit': re.compile('''
    ^ # action [quantity] ticket stop price limit price
    (?P<action>(buy|sell))            # entry action: buy or sell
    (?:(?P<quantity>\d+))?\s?         # quantity: optional, int
    (?P<ticker>\w+)                   # ticker: string
    \sstop\s
    (?P<stop_price>(?:\d+\.)?\d+)     # stop price: int or float
    \slimit\s
    (?P<limit_price>(?:\d+\.)?\d+)    # limit price: int or float
    $
    ''', re.VERBOSE),

    'exit': re.compile('''
    ^ # action at price or price
    (?P<action>(buy|sell|cover))      # exit action: buy, sell or cover
    \sat\s
    (?P<target_price>(?:\d+\.)?\d+)   # target price: int or float
    \sor\s
    (?P<stop_price>(?:\d+\.)?\d+)     # stop price: int or float
    $
    ''', re.VERBOSE),
}

def parse_args(args):
    entry_command, exit_command = args.command
    entry_match = REGEXES['limit'].search(entry_command) or REGEXES['stop_limit'].search(entry_command)
    exit_match = REGEXES['exit'].search(exit_command)
    if not entry_match or not exit_match:
        error()
    matches = Hash(**entry_match.groupdict())

    def create_entry(matches):

        price = float(matches.entry_price)
        quantity = int(matches.quantity) if matches.quantity else calculate_quantity(price, args.max)
        actions = {
            'buy': ACTION_BUY,
            'sell': ACTION_SHORT,
        }
        types = {
            None: TYPE_MARKET,
            'market': TYPE_MARKET,
            'limit': TYPE_LIMIT
        }
        return Order(action=ACTION_BUY if matches.action == 'buy' else ACTION_SHORT,
                     quantity=quantity,
                     ticker=matches.ticker.upper(),
                     type=types[matches.type],
                     price=price)

    def create_exit():
        pass

    # parse exit
    pattern = r'^(?P<action>(buy|sell)) at (?P<target_price>(?:\d+\.)?\d+) or (?P<stop_price>(?:\d+\.)?\d+)$'
    regex = re.compile(pattern)
    match = regex.search(exit)
    if not match:
        error()
    exit = Hash(**match.groupdict())
    exit.action = exit.action.upper()
    exit.target_price = float(exit.target_price)
    exit.stop_price = float(exit.stop_price)

    # validate inputs
    if entry.action == BUY:
        if not exit.target_price > exit.stop_price:
            target = exit.stop_price
            exit.stop_price = exit.target_price
            exit.target_price = target
        assert exit.action == SELL, 'exit action must be sell for buy orders'
        assert exit.target_price > entry.price, 'Target price must be greater than %.2f (%.2f given)' % (
            entry.price, exit.target_price
        )
        assert exit.stop_price < entry.price, 'Stop price must be less than %.2f (%.2f given)' % (
            entry.price, exit.stop_price
        )
    else:
        if not exit.target_price < exit.stop_price:
            target = exit.stop_price
            exit.stop_price = exit.target_price
            exit.target_price = target
        assert exit.action == BUY, 'exit action must be buy for sell orders'
        assert exit.target_price < entry.price, 'Target price must be less than %.2f (%.2f given)' % (
            entry.price, exit.target_price
        )
        assert exit.stop_price > entry.price, 'Stop price must be greater than %.2f (%.2f given)' % (
            entry.price, exit.stop_price
        )

    return entry, exit

def calculate_quantity(entry_price, max_amount, lot_size=100):
    def _calculate_quantity(lot_size):
        # use 95% of max_amount to account for commission/slippage
        quantity = (0.95 * max_amount) / entry_price
        return quantity - (quantity % lot_size)
    quantity = _calculate_quantity(lot_size)
    while not quantity:
        lot_size = lot_size / 10
        quantity = _calculate_quantity(lot_size)
    return int(quantity)

def pf(price):
    return '$%.2f' % price

def risk_reward(entry, exit, commission):
    return total_profit(entry, exit, commission) / risk(entry, exit, commission)

def order_summary(entry, exit, commission):
    data = (
        ['%(action)s %(quantity)s %(ticker)s' % entry.as_dict(), pf(entry.price), Color('{cyan}%s{/cyan}' % pf(cost(entry, exit, commission)))],
        ['50% Target', pf(half_target_price(entry, exit)), '+%s' % pf(half_target_profit(entry, exit, commission))],
        ['Target', pf(exit.target_price), '+%s' % pf(target_profit(entry, exit, commission))],
        ['Profit', '', Color('{green}+%s{/green}' % pf(total_profit(entry, exit, commission)))],
        ['Stop loss', pf(exit.stop_price), Color('{hired}-%s{/red}' % pf(risk(entry, exit, commission)))],
        ['Risk/Reward', '', Color('{%(color)s}%(risk_reward).1f to 1{/%(color)s}' % {
            'risk_reward': risk_reward(entry, exit, commission),
            'color': 'green' if risk_reward(entry, exit, commission) >= 3 else 'hired'
        })],
    )

    table = AsciiTable(data)
    table.inner_column_border = False
    print(table.table)

def cost(entry, exit, commission):
    return (entry.price * entry.quantity) + commission

def risk(entry, exit, commission):
    risk = entry.quantity * (entry.price - exit.stop_price)
    if risk < 0:
        risk = risk * -1
    return risk + (2 * commission)

def half_target_price(entry, exit):
    if entry.action == BUY:
        return entry.price + ((exit.target_price - entry.price) / 2)
    elif entry.action == SELL:
        return entry.price - ((entry.price - exit.target_price) / 2)
    raise Exception('Unrecognized action: %s' % entry.action)

def half_target_profit(entry, exit, commission):
    profit = (entry.quantity / 2) * (half_target_price(entry, exit) - entry.price)
    if profit < 0:
        profit = profit * -1
    return profit - commission

def target_profit(entry, exit, commission):
    profit = (entry.quantity / 2) * (exit.target_price - entry.price)
    if profit < 0:
        profit = profit * -1
    return profit - commission

def total_profit(entry, exit, commission):
    return half_target_profit(entry, exit, commission) + target_profit(entry, exit, commission) - commission

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='foo desc')

    def max_type(max):
        if 'k' in max.lower():
            return int(max.lower().replace('k', '')) * 1000
        return int(max)

    parser.add_argument('command', metavar='COMMAND', nargs='+', help='The buy and sell command')
    parser.add_argument('--max', default=MAX_AMOUNT, help='The maximum dollar amount to invest', type=max_type, required=False)
    parser.add_argument('--commission', default=COMMISSION, help='Commission charged per trade', type=float, required=False)
    parser.add_argument('--levels', default=SCALE_OUT_LEVELS, help='The number of scale-out levels', type=int, required=False)
    args = parser.parse_args()
    args.command = ' '.join(args.command).lower().split(', ')

    entry, exit = parse_args(args)

    order_summary(entry, exit, args.commission)
