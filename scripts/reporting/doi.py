#!/usr/bin/env python3

# http://habanero.readthedocs.io/en/latest/api.html

import sys
import os
import time
import pandas as pd
import hs_restclient as hsapi
import getpass
from habanero import counts
import multiprocessing as mp
import signal
import datetime

import argparse



class Timeout():
    """Timeout class using ALARM signal."""
    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()

def load_data(wrkdir):
    doipath = os.path.join(wrkdir, 'doi.pkl')
    return pandas.read_pickle(doipath)

def check_doi(q, out_q):
    while True:
        resid = q.get()
        if resid is None:
            return

        with Timeout(10):
            sysmeta = hs.getSystemMetadata(resid)
            published = sysmeta['published']
            if published:
                scimeta = hs.getScienceMetadata(resid)
                doi_url = next((item for item in scimeta['identifiers']
                                if item['name'] == 'doi'))['url']
                doi = '/'.join(doi_url.split('/')[-2:])

                print('|', end='', flush=True)
                out_q.put({'resid': resid, 'doi': doi})
            else:
                print('.', end='', flush=True)


def search_hs(hs, resources):

    print('\n--> searching HS for doi\'s')

    # configure the multiprocessing environment
    NCORE = mp.cpu_count()
    in_q = mp.Queue()
    out_q = mp.Queue()
    pool = mp.Pool(NCORE, initializer=check_doi,
                   initargs=(in_q, out_q))

    # build queue of resource ids for the pool workers
    for resid in resources:
        in_q.put(resid)

    # tell workers to exit
    for _ in range(NCORE):
        in_q.put(None)

    # wait for all processes to finish
    while not in_q.empty():
        time.sleep(1)

    # dequeue the out_q to prevent the underlying pipe from freezing join
    time.sleep(3)
    data = []
    while not out_q.empty():
        val = out_q.get()
        data.append(val)
    pool.close()
    pool.join()

    df = pd.DataFrame(data)

    return df


def split_date_range(n):
    begin = datetime.date(2015, 5, 1)
    end = datetime.datetime.now().date()
    intervals = n

    date_list = []
    delta = (end - begin)/intervals
    st = begin
    for i in range(1, intervals + 1):
        et = begin+i*delta
        date_list.append([st, et])
        st = et

    return date_list


def query_resource_ids(in_q, out_q, hs):
    while True:
        st, et = in_q.get()
        if st is None:
            break

        resources = hs.resources(from_date=st, to_date=et)
        for resource in resources:
            resid = resource['resource_id']
            out_q.put(resid)
            print('.', end='', flush=True)


def collect_resource_ids(hs):

    NCORE = mp.cpu_count()
    in_q = mp.Queue()
    out_q = mp.Queue()

    print('--> populating job queue...', end='')
    # split the date range of HS resources
    dates = split_date_range(1000)
    for date in dates:
        in_q.put(date)
    # tell workers to exit
    for _ in range(NCORE):
        in_q.put([None, None])
    print('done')

    print('--> collecting resource ids')
    pool = mp.Pool(NCORE, initializer=query_resource_ids,
                   initargs=(in_q, out_q, hs))

    # wait for all processes to finish
    while not in_q.empty():
        time.sleep(1)

    # dequeue out_q to prevent join from freezing
    res_ids = []
    while not out_q.empty():
        val = out_q.get()
        res_ids.append(val)
    pool.close()
    pool.join()
    return res_ids


def print_statistics(workingdir):

    df = load_data(wrkdir)
    print('\n'+50*'-')
    print('Resource Citation Summary')
    print(50*'-')

    # select all resources that have been cited
    cited_resources = df[df.citations > 0]
    print('{:<40}{:<10}'.format('ResourceID', 'Citation Count'))
    for idx, row in cited_resources.iterrows():
        print('{:<40}{:<10}'.format(row.resid, row.citations))
    print(50*'-')


def authenticate():
    tries = 0
    host = input('Enter host (or www): ') or 'www.hydroshare.org'
    while 1:
        u = input('Enter HS username: ')
        p = getpass.getpass('Enter HS password: ')
        auth = hsapi.HydroShareAuthBasic(username=u, password=p)
        hs = hsapi.HydroShare(hostname=host, auth=auth)
        try:
            hs.getUserInfo()
            break
        except hsapi.exceptions.HydroShareHTTPException:
            print('Authentication failed, attempt %d' % (tries+1))
            tries += 1

        if tries >= 3:
            print('Number of attempts exceeded, exiting')
            sys.exit(1)
        print('')

        return hs

def collect_data(wrkdir):

    hs = authenticate()

    resources = collect_resource_ids(hs)
    df = search_hs(hs, resources)

    # save results to at data frame
    pklpath = os.path.join(wrkdir, 'doi.pkl')
    csvpath = os.path.join(wrkdir, 'doi.csv')
    df.to_pickle(pklpath)
    df.to_csv(csvpath)


def calculate_stats(wrkdir):
    #-----------
    # calc stats
    #-----------
        
    df = load_data(wrkdir)

    # calculation number of citations for each resource
    citations = []
    for idx, row in df.iterrows():
        cites = counts.citation_count(doi=row.doi)
        citations.append(cites)
        print('%s => %s' % (row.resid, cites))
    df['citations'] = citations
    
    # calculate number of cites for each paper, i.e. 2nd citations
    cited_resources = df[df.citations > 0]
    print(cited_resources)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--working-dir',
                        help='path to working directory',
                        required=True)
    parser.add_argument('-c',
                        help='force recollect data',
                        action='store_true')
    parser.add_argument('-p',
                        help='print statistics',
                        action='store_true')
    args = parser.parse_args()

    workingdir = args.working_dir

    # collect data
    doipath = os.path.join(workingdir, 'doi.pkl')
    if args.c or not os.path.exists(doipath):
        collect_data(workingdir)

    if args.p:
        calculate_stats(workingdir)
        print_statistics(workingdir)








