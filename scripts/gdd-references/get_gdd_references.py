#!/usr/bin/env python

"""
Test URL:
    https://geodeepdive.org/api/snippets?full_results=true&inclusive=true&term=CUAHSI

"""

import sys
import json
import pandas
import requests
import argparse

results = []

def search_gdd(terms):

    base = 'https://geodeepdive.org/api/snippets'

#    full_results=true&inclusive=true&min_published=2020-01-01&clean
    params = {'term': '',
              'full_results': True,
              'inclusive': True
              }

    for term in terms:
        params['term'] = term

        # make request
        r = requests.get(base, params=params)

        if r.status_code == 200:
            # load the data
            data = json.loads(r.content)
            
            results.append(pandas.from_dict(data['success']['data']))

            # get the next page
            next_page = data['success']['next_page']
            # todo call recursively

            import pdb; pdb.set_trace()
        else:
            print(r.status_code)
            break


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-f',
                   default='',
                   help='path to list of search terms')
    p.add_argument('-t',
                   default='',
                   nargs='+',
                   help='space separated list of search terms')

    args = p.parse_args()

    # exit early if -f and -t are not provided
    if not (args.f or args.t):
        print('Must supply either -f or -t argument')
        p.print_usage()
        sys.exit(1)

    if args.f:
        with open(args.f, 'r') as f:
            terms = [l.strip() for l in f.readlines()]
    elif args.t:
        terms = args.t

    search_gdd(terms)


