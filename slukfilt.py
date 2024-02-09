#!/usr/bin/env python3
from bs4 import BeautifulSoup
import sys

def slukfilt(slukhtml):
    sluksoup = BeautifulSoup(slukhtml, 'html.parser')
    for t in sluksoup.find_all('table', class_='hidden-print'):
        t.extract()
    for s in sluksoup.find_all('script'):
        s.extract()
    return sluksoup

if __name__ == '__main__':
    with open(0, 'rb') as f:
        sk = f.read()
    print(str(slukfilt(sk)))
