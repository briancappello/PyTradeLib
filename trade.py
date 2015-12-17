from __future__ import print_function

import re
import sys

from colorclass import Color
from terminaltables import AsciiTable

from pytradelib.hash import Hash
from pytradelib.settings import COMMISSION, MAX_AMOUNT


def error():
    print('Command should be in the format of:\n <buy|sell> [quantity] <ticker> at <price>, <sell|buy> at <target_price> or <stop_price>')
    sys.exit(1)

BUY = 'BUY'
SELL = 'SELL'

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

    entry = Hash(**entry_match.groupdict())
    entry.action = entry.action.upper()
    entry.ticker = entry.ticker.upper()
    if 'price' in entry:
        entry.price = float(entry.price)
    else:
        entry.stop_price = float(entry.stop_price)
        entry.price = float(entry.limit_price)
    entry.quantity = int(entry.quantity) if entry.quantity\
        else calculate_quantity(entry.price, args.max)

    exit = Hash(**exit_match.groupdict())
    exit.action = exit.action.upper()
    exit.target_price = float(exit.target_price)
    exit.stop_price = float(exit.stop_price)

    # validate inputs
    if entry.action == BUY:
        assert exit.action == SELL, 'exit action must be sell for buy orders'
        if not exit.target_price > exit.stop_price:
            target = exit.stop_price
            exit.stop_price = exit.target_price
            exit.target_price = target
        assert exit.target_price > entry.price, 'Target price must be greater than %s (%s given)' % (
            pf(entry.price), pf(exit.target_price)
        )
        assert exit.stop_price < entry.price, 'Stop price must be less than %s (%s given)' % (
            pf(entry.price), pf(exit.stop_price)
        )
        if 'stop_price' in entry:
            assert entry.stop_price < entry.price, 'Entry stop price must be less than %s (%s given)' % (
                pf(entry.price), pf(entry.stop_price)
            )
    else:  # entry.action == SELL
        assert exit.action == BUY, 'exit action must be buy for sell orders'
        if not exit.target_price < exit.stop_price:
            target = exit.stop_price
            exit.stop_price = exit.target_price
            exit.target_price = target
        assert exit.target_price < entry.price, 'Target price must be less than %s (%s given)' % (
            pf(entry.price), pf(exit.target_price)
        )
        assert exit.stop_price > entry.price, 'Stop price must be greater than %s (%s given)' % (
            pf(entry.price), pf(exit.stop_price)
        )
        if 'stop_price' in entry:
            assert entry.stop_price < entry.price, 'Entry stop price must be greater than %s (%s given)' % (
                pf(entry.price), pf(entry.stop_price)
            )
    return entry, exit


def calculate_quantity(entry_price, max_amount, lot_size=100):
    def _calculate_quantity(lot_size):
        # use 95% of max_amount to account for commission/slippage
        quantity = (0.95 * max_amount) / entry_price
        return quantity - (quantity % lot_size)
    quantity = _calculate_quantity(lot_size)
    while not quantity:
        lot_size /= 10
        quantity = _calculate_quantity(lot_size)
    return int(quantity)


def pf(price):
    return '$%.2f' % price


def risk_reward(entry, exit, commission):
    return total_profit(entry, exit, commission) / risk(entry, exit, commission)


def order_summary(entry, exit, commission):
    data = []
    if 'stop_price' in entry:
        data.append(
            ['%(action)s %(quantity)s %(ticker)s STOP $%(stop_price).2f LIMIT' % entry.as_dict(),
             pf(entry.price),
             Color('{cyan}%s{/cyan}' % pf(cost(entry, exit, commission)))]
        )
    else:
        data.append(
            ['%(action)s %(quantity)s %(ticker)s LIMIT' % entry.as_dict(),
             pf(entry.price),
             Color('{cyan}%s{/cyan}' % pf(cost(entry, exit, commission)))]
        )
    data.extend([
        ['50% Target', pf(half_target_price(entry, exit)), '+%s' % pf(half_target_profit(entry, exit, commission))],
        ['Target', pf(exit.target_price), '+%s' % pf(target_profit(entry, exit, commission))],
        ['Profit', '', Color('{green}+%s{/green}' % pf(total_profit(entry, exit, commission)))],
        ['Stop loss', pf(exit.stop_price), Color('{hired}-%s{/red}' % pf(risk(entry, exit, commission)))],
        ['Risk/Reward', '', Color('{%(color)s}%(risk_reward).1f to 1{/%(color)s}' % {
            'risk_reward': risk_reward(entry, exit, commission),
            'color': 'green' if risk_reward(entry, exit, commission) >= 3 else 'hired'
        })],
    ])

    table = AsciiTable(data)
    table.inner_column_border = False
    print(table.table)


def cost(entry, exit, commission):
    return (entry.price * entry.quantity) + commission


def risk(entry, exit, commission):
    risk = entry.quantity * (entry.price - exit.stop_price)
    if risk < 0:
        risk *= -1
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
        profit *= -1
    return profit - commission


def target_profit(entry, exit, commission):
    profit = (entry.quantity / 2) * (exit.target_price - entry.price)
    if profit < 0:
        profit *= -1
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
    args = parser.parse_args()
    args.command = ' '.join(args.command).lower().split(', ')

    entry, exit = parse_args(args)

    order_summary(entry, exit, args.commission)
