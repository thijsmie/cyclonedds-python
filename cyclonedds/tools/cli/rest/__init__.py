import urllib.request as req
import json


def scan_endpoint(url):
    with req.urlopen(url) as f:
        print(f.read().decode('utf-8'))
