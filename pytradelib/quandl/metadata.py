from __future__ import print_function

import csv
import requests
import pandas as pd
from zipfile import ZipFile
from cStringIO import StringIO


URL = 'https://www.quandl.com/api/v3/databases/%(dataset)s/codes'


def dataset_url(dataset):
    return URL % {'dataset': dataset}


def download_file(url):
    r = requests.get(url)
    if r.status_code == 200:
        return StringIO(r.content)


def unzip(file_):
    d = unzip_files(file_)
    return d[d.keys()[0]]


def unzip_files(file_):
    d = {}
    with ZipFile(file_, 'r') as zipfile:
        for filename in zipfile.namelist():
            d[filename] = zipfile.read(filename)
    return d


def csv_rows(str):
    for row in csv.reader(StringIO(str)):
        yield row


def csv_dicts(str, fieldnames=None):
    for d in csv.DictReader(StringIO(str), fieldnames=fieldnames):
        yield d


def get_symbols_list(dataset):
    csv_ = unzip(download_file(dataset_url(dataset)))
    return map(lambda x: x[0].replace(dataset + '/', ''), csv_rows(csv_))


def get_symbols_dict(dataset):
    csv_ = unzip(download_file(dataset_url(dataset)))
    return dict(csv_rows(csv_))


def get_symbols_df(dataset):
    csv_ = unzip(download_file(dataset_url(dataset)))
    df = pd.read_csv(StringIO(csv_), header=None, names=['symbol', 'company'])
    df.symbol = df.symbols.map(lambda x: x.replace(dataset + '/', ''))
    df.company = df.company.map(lambda x: x.replace('Prices, Dividends, Splits and Trading Volume', ''))
    return df
