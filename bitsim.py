#!/usr/bin/env python2
import csv
import time
import urllib
import argparse

from datetime import datetime
from collections import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument('--csv', help="Use specified CSV file")
parser.add_argument('--save', action='store_true',
    help="Save BTC remainder each iteration")
parser.add_argument('deposit', type=float, default=1.00,
    help="Deposit amount (default: %(default)s)")
parser.add_argument('-c', '--currency', default='USD',
    help="Currency code (default: %(default)s)")
parser.add_argument('start_date',
    help="Date to start transactions")
parser.add_argument('end_date',
    help="Date to end transactions (default: %(default)s)")
parser.add_argument('interval', type=int,
    help="Interval to make transactions")
parser.add_argument('--quiet', action='store_true',
    help="Output only final balance")
args = parser.parse_args()

deposit = round(float(args.deposit), 2)
currency = args.currency.upper()

data = OrderedDict()
if args.csv:
    csvfile = open(args.csv, 'rb')
else:
    url = "https://api.bitcoinaverage.com/history/{}/per_day_all_time_history.csv".format(currency)
    csvfile = urllib.urlopen(url)
init = True
for row in csv.reader(csvfile):
    if init:
        init = False
        continue
    date = time.strptime(row[0], '%Y-%m-%d %H:%M:%S')
    date = datetime.fromtimestamp(time.mktime(date))
    data[date] = tuple(row[1:]) # {date: (low, high, avg, vol)}

start_date = time.mktime(time.strptime(args.start_date, '%Y-%m-%d'))
start_date = datetime.fromtimestamp(start_date)
end_date   = time.mktime(time.strptime(args.end_date, '%Y-%m-%d'))
end_date   = datetime.fromtimestamp(end_date)
interval   = args.interval

balance = 0.00
btc_balance = 0

iteration = 0
for date, row in data.items():
    # continue if date not within range
    if date < start_date or date > end_date:
        continue

    rate = float(row[2])
    date = date.strftime('%Y-%m-%d')

    # buy if first iteration (0)
    if not iteration:
        balance -= deposit
        amount = (1 / rate) * deposit
        btc_balance += amount
        if not args.quiet:
            print "[{date}] Buying {deposit:.2f} {currency} @ {rate:.2f} {currency} per BTC = {amount} BTC ({balance:.2f} {currency} / {btc_balance} BTC)".format(**locals())
    # sell if last iteration
    elif iteration == interval:
        btc_amount = btc_balance if not args.save else (1 / rate) * deposit
        # sell everything if insufficient funds
        if btc_balance < btc_amount:
            btc_amount = btc_balance        
        btc_balance -= btc_amount        
        amount = btc_amount * rate
        balance += amount
        profit = btc_balance * rate
        balance += profit
        if not args.quiet:
            print "[{date}] Selling {btc_amount} BTC @ {rate:.2f} {currency} per BTC = {amount:.2f} {currency} ({balance:.2f} {currency} / {btc_balance} BTC)\n".format(**locals())
        iteration = 0
        continue
    # wait if iterating
    else:
        amount = btc_balance * rate
        profit = balance + amount
        if not args.quiet:
            print "[{date}] Waiting {btc_balance} BTC @ {rate:.2f} = {amount:.2f} {currency} ({profit:+.2f} {currency})".format(**locals())
    iteration += 1

if btc_balance:
    amount = btc_balance * rate
    balance += amount
    if not args.quiet:
        print "Selling remaining {btc_balance} BTC @ {rate:.2f} = {amount:.2f} {currency}\n".format(**locals())

if not args.quiet:
    print "Final balance: {balance:.2f} {currency}".format(**locals())
else:
    print "{:.2f}".format(balance)
